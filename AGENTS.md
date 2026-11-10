# AGENTS.md — CareerLens AI

Panduan kerja untuk agen AI/kontributor di repositori ini. Baca `docs/rancangan.md` sebagai acuan utama.

## Ringkasan proyek

CareerLens AI (*Your Career, Analyzed by AI*) adalah platform analisis CV dan job matching:

- **CV Upload & Parser** — PDF/DOCX → teks → data terstruktur yang bisa dikoreksi user.
- **CV Analyzer** — skor 0–100 berbasis rubrik terukur + saran perbaikan.
- **Skill Analyzer** — skill terdeteksi per kategori + skill gap.
- **Job Matcher** — persentase kecocokan, matched/missing skills, alasan.
- **Dashboard** — gauge skor, breakdown, radar skill, rekomendasi lowongan, roadmap belajar.

Cakupan saat ini: **MVP** (CV Analyzer + Job Matcher). Fase 2 (CV Improver, Cover Letter Generator, Interview Simulator, Career Path Prediction) di luar MVP.

## Status fase

| Fase | Fokus | Status |
|---|---|---|
| 1 | Fondasi, Docker, DB, auth, UI dasar | Selesai |
| 2 | Parser CV, skill extraction, halaman review | Selesai |
| 3 | Scoring rubrik + saran LLM | Selesai |
| 4 | Seed 40 lowongan + job matcher | Selesai |
| 5 | Dashboard gabungan, riwayat/compare, skill gap & roadmap | Selesai |
| 6 | Testing, hardening, dokumentasi, demo | Berjalan |

## Tech stack

| Bagian | Teknologi |
|---|---|
| Frontend | React + Vite |
| Styling | Tailwind CSS |
| Visualisasi | Recharts (lazy-loaded per halaman) |
| Backend | Python + FastAPI |
| NLP | Aturan berbasis regex + taksonomi alias (`services/nlp.py`) |
| Parser | pdfplumber, python-docx |
| Matching | Sentence Transformers (`all-MiniLM-L6-v2`) |
| LLM | LLM API — hanya untuk teks saran/penjelasan |
| Database | PostgreSQL (+ pgvector opsional) |
| ORM | SQLAlchemy |
| Testing | pytest |
| Dev | docker-compose |
| CI | GitHub Actions |

## Struktur folder

```
careerlens/
├─ .github/workflows/     (ci.yml: pytest + npm run build)
├─ AGENTS.md
├─ README.md
├─ LICENSE
├─ demo/                  (CV contoh fiktif DOCX/PDF + instruksi demo)
├─ docs/                  (rancangan.md, rencana-kerja.md, security-audit.md, screenshots/)
├─ backend/
│  ├─ alembic/            (migrasi database)
│  ├─ app/
│  │  ├─ main.py
│  │  ├─ api/             (routers: auth, cv, profile, analysis, jobs, skills, dashboard)
│  │  ├─ core/            (config, security, rate_limit)
│  │  ├─ models/          (SQLAlchemy)
│  │  ├─ schemas/         (Pydantic)
│  │  ├─ services/        (parser, nlp, scoring, matching, llm, profile_store)
│  │  └─ data/            (skills.json, jobs_seed.json, learning_resources.json)
│  ├─ tests/              (pytest + fixtures)
│  └─ requirements.txt
├─ frontend/
│  └─ src/                (pages, components, hooks, api)
├─ docker-compose.yml
└─ .env.example
```

## Perintah

Backend (dari `backend/`):

```bash
python -m venv venv
venv\Scripts\activate        # Windows; source venv/bin/activate di Linux/macOS
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
pytest -q                    # semua test (model asli tidak diunduh)
pytest tests/test_scoring.py -q
pytest -m slow -q            # test yang memakai model sentence-transformers asli
```

Frontend (dari `frontend/`):

```bash
npm install
npm run dev                  # Vite dev server
npm run build
```

Seluruh stack:

```bash
docker compose up --build    # API :8000, frontend :5173, Postgres :5432
```

## Aturan wajib (non-negotiable)

1. **Angka dihitung kode, bukan LLM.** Skor CV (0–100) dan persentase match WAJIB dihitung kode berdasarkan rubrik di `docs/rancangan.md` §5–§6. LLM hanya menghasilkan teks saran/penjelasan. LLM tidak boleh menentukan, menyesuaikan, atau menimpa angka apa pun.
2. **Jangan kirim nama/kontak user ke LLM.** Sebelum memanggil LLM, anonimkan: hapus/hapus-identitas nama, email, telepon, alamat, tautan profil pribadi, dan nama perusahaan spesifik bila tidak diperlukan.
3. **Validasi upload.** Hanya PDF/DOCX, maksimal **5 MB**, cek **MIME** (magic bytes), bukan sekadar ekstensi. Tolak file lain/kosong/rusak dengan error yang jelas.
4. **Setiap fitur wajib punya unit test (pytest).** Tulis test bersama implementasi, bukan menyusul. Target: setiap fungsi rubrik, parser, matcher, validasi, dan endpoint punya test.
5. **Satu fase per sesi.** Kerjakan hanya fase yang diminta. Jangan mengubah, memindahkan, atau me-refactor bagian dari fase lain tanpa permintaan eksplisit.
6. **Jangan log PII.** Nama, email, telepon, alamat, dan isi CV tidak boleh masuk log aplikasi. Pesan error autentikasi harus generik.
7. **Production wajib aman.** `ENVIRONMENT=production` menolak start jika `JWT_SECRET` masih nilai contoh/kurang dari 32 karakter atau `CORS_ORIGINS` berisi `*`.
8. **Rate limit auth.** `/auth/login` dan `/auth/register` dibatasi `RATE_LIMIT_PER_MINUTE` per IP (default 10/menit).
9. **Hapus data = hapus semua.** `DELETE /auth/me` menghapus user, CV, profil, skill, analisis, job match, dan file fisik. `DELETE /cv/{id}` menghapus CV beserta turunannya.

## Prinsip implementasi

- Setiap kriteria rubrik = fungsi terpisah yang mengembalikan `(skor, alasan)`.
- `score_breakdown` disimpan sebagai JSON agar bisa ditampilkan per kriteria.
- Matched/missing skills dihasilkan dari perbandingan himpunan, tanpa LLM.
- Rahasia (API key, JWT secret, kredensial DB) hanya di `.env`; jangan pernah di-commit.
- CV hanya bisa diakses pemiliknya; sediakan hapus CV beserta seluruh turunannya.
- Ikuti gaya kode di sekitarnya; jangan menambah komentar yang tidak diminta.
