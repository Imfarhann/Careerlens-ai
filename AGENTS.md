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

## Tech stack

| Bagian | Teknologi |
|---|---|
| Frontend | React + Vite |
| Styling | Tailwind CSS |
| Visualisasi | Recharts |
| Backend | Python + FastAPI |
| NLP | spaCy |
| Parser | pdfplumber, python-docx |
| Matching | Sentence Transformers (`all-MiniLM-L6-v2`) |
| LLM | LLM API — hanya untuk teks saran/penjelasan |
| Database | PostgreSQL (+ pgvector opsional) |
| ORM | SQLAlchemy |
| Testing | pytest |
| Dev | docker-compose |

## Struktur folder

```
careerlens/
├─ AGENTS.md
├─ docs/                  (rancangan.md, rencana-kerja.md)
├─ backend/
│  ├─ app/
│  │  ├─ main.py
│  │  ├─ api/             (routers: auth, cv, profile, analysis, jobs, skills)
│  │  ├─ core/            (config, security)
│  │  ├─ models/          (SQLAlchemy)
│  │  ├─ schemas/         (Pydantic)
│  │  ├─ services/        (parser, nlp, scoring, matching, llm)
│  │  └─ data/            (skills.json, jobs_seed.json, learning_resources)
│  ├─ tests/              (pytest)
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
python -m spacy download en_core_web_sm
uvicorn app.main:app --reload --port 8000
pytest -q                    # semua test
pytest tests/test_scoring.py -q
```

Frontend (dari `frontend/`):

```bash
npm install
npm run dev                  # Vite dev server
npm run build
npm run test                 # jika test frontend ditambahkan
```

Seluruh stack:

```bash
docker compose up --build    # API :8000, frontend :5173, Postgres :5432
```

> Perintah di atas adalah target akhir MVP. Sebagian belum tersedia sampai fase terkait selesai.

## Aturan wajib (non-negotiable)

1. **Angka dihitung kode, bukan LLM.** Skor CV (0–100) dan persentase match WAJIB dihitung kode berdasarkan rubrik di `docs/rancangan.md` §5–§6. LLM hanya menghasilkan teks saran/penjelasan. LLM tidak boleh menentukan, menyesuaikan, atau menimpa angka apa pun.
2. **Jangan kirim nama/kontak user ke LLM.** Sebelum memanggil LLM, anonimkan: hapus/hapus-identitas nama, email, telepon, alamat, tautan profil pribadi, dan nama perusahaan spesifik bila tidak diperlukan.
3. **Validasi upload.** Hanya PDF/DOCX, maksimal **5 MB**, cek **MIME** (magic bytes), bukan sekadar ekstensi. Tolak file lain/kosong/rusak dengan error yang jelas.
4. **Setiap fitur wajib punya unit test (pytest).** Tulis test bersama implementasi, bukan menyusul. Target: setiap fungsi rubrik, parser, matcher, validasi, dan endpoint punya test.
5. **Satu fase per sesi.** Kerjakan hanya fase yang diminta. Jangan mengubah, memindahkan, atau me-refactor bagian dari fase lain tanpa permintaan eksplisit.

## Prinsip implementasi

- Setiap kriteria rubrik = fungsi terpisah yang mengembalikan `(skor, alasan)`.
- `score_breakdown` disimpan sebagai JSON agar bisa ditampilkan per kriteria.
- Matched/missing skills dihasilkan dari perbandingan himpunan, tanpa LLM.
- Rahasia (API key, JWT secret, kredensial DB) hanya di `.env`; jangan pernah di-commit.
- CV hanya bisa diakses pemiliknya; sediakan hapus CV beserta seluruh turunannya.
- Ikuti gaya kode di sekitarnya; jangan menambah komentar yang tidak diminta.
