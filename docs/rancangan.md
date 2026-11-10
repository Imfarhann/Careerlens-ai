# CareerLens AI — Rancangan Proyek

Tagline: *Your Career, Analyzed by AI.*

Platform AI yang menganalisis CV, mengidentifikasi skill, menemukan skill gap, dan mencocokkan pengguna dengan lowongan pekerjaan.

## 1. Keputusan desain

- Cakupan: **MVP lengkap** (CV Analyzer + Job Matcher)
- Data lowongan: **database buatan sendiri** (seed 30-50 lowongan)
- Gaya UI: **Modern SaaS, dark navy + blue**
- Fase 2 (setelah MVP): CV Improver, Cover Letter Generator, Interview Simulator, Career Path Prediction

## 2. Ruang lingkup MVP

| Modul | Isi |
|---|---|
| CV Upload & Parser | Upload PDF/DOCX, ekstraksi teks, data terstruktur yang bisa dikoreksi user |
| CV Analyzer | Skor 0-100 dengan rubrik terukur, plus saran perbaikan |
| Skill Analyzer | Skill terdeteksi, dikelompokkan per kategori, plus skill gap |
| Job Matcher | Persentase kecocokan, alasan, perbandingan skill |
| Dashboard | Skor, radar skill, rekomendasi lowongan, roadmap belajar sederhana |

## 3. Arsitektur

```
React (Vite + Tailwind + Recharts)
        |  REST + JWT
FastAPI -- Auth -- Upload Validator
   |
   +- Parser Service   (pdfplumber / python-docx -> teks)
   +- NLP Service      (spaCy + skill taxonomy -> data terstruktur)
   +- Scoring Service  (rubrik berbasis aturan)
   +- Matching Service (Sentence Transformers + skill overlap)
   +- LLM Service      (hanya untuk teks saran, bukan angka)
        |
PostgreSQL (+ pgvector untuk embedding, opsional)
```

**Prinsip utama:** angka (skor, persen match) dihitung oleh kode dengan aturan yang jelas. LLM hanya menulis penjelasan dan saran.

## 4. Tech stack

| Bagian | Teknologi |
|---|---|
| Frontend | React + Vite |
| Styling | Tailwind CSS |
| Visualisasi | Recharts |
| Backend | Python + FastAPI |
| NLP | spaCy |
| Matching | Sentence Transformers (`all-MiniLM-L6-v2`) |
| LLM | LLM API (hanya untuk saran teks) |
| Database | PostgreSQL |
| ORM | SQLAlchemy |
| Dev | docker-compose |

## 5. Rubrik skor CV (total 100)

| Kriteria | Bobot | Cara menghitung |
|---|---|---|
| Kelengkapan section | 25 | Ada kontak, pendidikan, pengalaman/project, skill, ringkasan (5 poin per section) |
| Kualitas deskripsi | 25 | Persentase bullet yang diawali kata kerja aksi dan memuat angka/hasil |
| Keterbacaan ATS | 20 | Teks bisa diekstrak, bukan gambar, heading standar, tanpa tabel rumit |
| Skill & relevansi | 15 | Jumlah skill terdeteksi dan keragaman kategori |
| Format & panjang | 15 | 1-2 halaman, konsistensi format tanggal, ada link GitHub/LinkedIn |

Aturan implementasi:
- Setiap kriteria adalah fungsi terpisah yang mengembalikan `(skor, alasan)`.
- Hasil disimpan sebagai `score_breakdown` (JSON) agar bisa ditampilkan di dashboard.
- Setiap fungsi wajib punya unit test.

## 6. Algoritma Job Matching

```
match_score = 0.6 * skill_coverage + 0.4 * semantic_similarity
```

- **skill_coverage:** persentase skill wajib lowongan yang dimiliki user. Skill wajib berbobot lebih tinggi daripada skill nilai tambah.
- **semantic_similarity:** cosine similarity antara embedding ringkasan profil user dan deskripsi lowongan.
- **Alasan match:** `matched_skills` dan `missing_skills` dihasilkan dari perbandingan set, tanpa LLM.

## 7. Skema database

| Tabel | Kolom utama |
|---|---|
| `users` | id, email, password_hash, created_at |
| `cvs` | id, user_id, file_path, raw_text, uploaded_at |
| `profiles` | id, cv_id, name, education (JSON), experience (JSON), projects (JSON) |
| `skills` | id, name, category, aliases |
| `user_skills` | profile_id, skill_id, level (opsional) |
| `jobs` | id, title, company, description, embedding |
| `job_skills` | job_id, skill_id, is_required |
| `analyses` | id, cv_id, total_score, score_breakdown (JSON), suggestions (JSON) |
| `job_matches` | analysis_id, job_id, match_score, matched_skills, missing_skills |
| `learning_resources` | id, skill_id, title, url |

## 8. Endpoint API

```
POST   /auth/register
POST   /auth/login
POST   /cv/upload                 -> validasi, parse, return profile
PUT    /profile/{id}              -> koreksi hasil ekstraksi
POST   /analysis/{cv_id}          -> hitung skor + saran
GET    /analysis/{id}
GET    /jobs/match/{analysis_id}  -> daftar lowongan + persen
GET    /skills/gap/{analysis_id}
DELETE /cv/{id}                   -> hapus CV (privasi)
GET    /health
```

## 9. Struktur folder

```
careerlens/
+- AGENTS.md
+- docs/rancangan.md
+- backend/
|  +- app/
|  |  +- main.py
|  |  +- api/          (routers)
|  |  +- core/         (config, security)
|  |  +- models/       (SQLAlchemy)
|  |  +- schemas/      (Pydantic)
|  |  +- services/     (parser, nlp, scoring, matching, llm)
|  |  +- data/         (skills.json, jobs_seed.json)
|  +- tests/
|  +- requirements.txt
+- frontend/
|  +- src/ (pages, components, hooks, api)
+- docker-compose.yml
```

## 10. Halaman frontend

1. **Landing/Login**
2. **Upload CV:** drag & drop dengan progress
3. **Review hasil ekstraksi:** form untuk mengoreksi data
4. **Dashboard:** gauge skor, bar breakdown, radar skill, kartu saran
5. **Job Matches:** daftar lowongan dengan persen, detail skill cocok dan kurang
6. **Skill Gap & Roadmap**

Palet: navy `#0B1220`, surface `#111A2E`, aksen biru `#3B82F6`, hijau untuk skor tinggi, kuning/merah untuk peringatan.

## 11. Keamanan dan privasi

- Autentikasi JWT; CV hanya bisa diakses pemiliknya.
- Validasi tipe dan ukuran file (maks. 5 MB), cek MIME, bukan sekadar ekstensi.
- Tombol hapus CV dan seluruh datanya.
- Jangan kirim data pribadi (nama, email, telepon) ke LLM; anonimkan dulu.
- Simpan rahasia (API key, JWT secret) di `.env`, jangan di-commit.

## 12. Jadwal (±6 minggu)

| Minggu | Target |
|---|---|
| 1 | Setup repo, Docker, DB, auth, desain UI |
| 2 | Parser PDF/DOCX + skill extraction + halaman review |
| 3 | Scoring rubrik + saran LLM |
| 4 | Seed 30-50 lowongan + Job Matcher |
| 5 | Dashboard, grafik, skill gap |
| 6 | Testing, perbaikan, deploy, README dan demo |

## 13. Kriteria selesai (definition of done)

- Semua endpoint di bagian 8 berfungsi dan punya test.
- Skor CV dapat dijelaskan per kriteria sesuai rubrik.
- Job matcher mengembalikan persen, skill cocok, dan skill kurang.
- Aplikasi bisa dijalankan dengan `docker-compose up`.
- README berisi screenshot, penjelasan rubrik, dan CV contoh untuk demo.
