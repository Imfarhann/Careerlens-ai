# Rencana Kerja — CareerLens AI (MVP)

Acuan: `docs/rancangan.md` §12 (jadwal ±6 minggu) dan §13 (definition of done).
Satu sesi = satu fase. Fase berikutnya baru dimulai setelah fase sebelumnya disetujui.

## Aturan kerja

- Setiap fase selesai harus: kode berjalan, `pytest -q` hijau, dan ringkasan hasil.
- Test ditulis bersama implementasi, bukan menyusul.
- Tidak menyentuh file/di luar cakupan fase tanpa persetujuan.
- Angka (skor, persen match) selalu dari kode; LLM hanya teks.

---

## Fase 1 — Fondasi: repo, Docker, DB, auth, desain UI (Minggu 1)

**Tujuan:** kerangka aplikasi bisa dijalankan end-to-end (kosong tapi hidup).

**Deliverable**
- Struktur `backend/app/{api,core,models,schemas,services,data}`, `backend/tests/`, `frontend/src/`.
- `backend/requirements.txt`, `.env.example` (DB URL, JWT secret, LLM key), `docker-compose.yml` (Postgres + API + frontend), `Dockerfile` masing-masing.
- `core/config.py` (pydantic-settings), `core/security.py` (hash password, JWT), `main.py` + `GET /health`.
- Model & migrasi awal: `users`; endpoint `POST /auth/register`, `POST /auth/login`.
- Frontend scaffold Vite + React + Tailwind: token warna navy/surface/biru, halaman Landing/Login + routing dasar.

**Test**
- `/health`, register (duplikat email, password lemah), login (sukses/gagal), proteksi route dengan JWT, hashing password.

**Selesai bila:** `docker compose up --build` menyalakan DB + API, `/health` OK, register → login → dapat token dari UI.

---

## Fase 2 — Upload, parser, skill extraction, halaman review (Minggu 2)

**Tujuan:** CV PDF/DOCX masuk, tervalidasi, terparse, dan bisa dikoreksi user.

**Deliverable**
- Upload validator: PDF/DOCX saja, maks 5 MB, cek MIME/magic bytes, tolak file kosong/rusak.
- `services/parser.py`: pdfplumber & python-docx → teks + deteksi section (kontak, ringkasan, pendidikan, pengalaman, project, skill).
- `data/skills.json` (taksonomi skill + alias + kategori) dan `services/nlp.py` (spaCy + pencocokan alias) → skill per kategori.
- Model `cvs`, `profiles`, `skills`, `user_skills`; `POST /cv/upload` (simpan file + raw_text, return profile), `PUT /profile/{id}`, `DELETE /cv/{id}` dasar.
- Frontend: halaman Upload (drag & drop + progress) dan Review hasil ekstraksi (form koreksi).

**Test**
- Validator (ekstensi palsu, >5 MB, file kosong, magic bytes benar/salah).
- Parser dengan fixture PDF/DOCX; section splitter; skill extractor (alias, case, duplikat).
- Endpoint upload/profile (termasuk akses milik user lain → 403/404).

**Selesai bila:** upload CV contoh → teks & skill terdeteksi → user bisa koreksi dan simpan.

---

## Fase 3 — Scoring rubrik + saran LLM (Minggu 3)

**Tujuan:** skor 0–100 yang dapat dijelaskan per kriteria, plus saran teks.

**Deliverable**
- `services/scoring.py`: 5 fungsi terpisah, masing-masing `(skor, alasan)` + bobot:
  kelengkapan section 25, kualitas deskripsi 25, keterbacaan ATS 20, skill & relevansi 15, format & panjang 15.
- Agregator → `total_score` + `score_breakdown` (JSON) sesuai rubrik §5.
- Model `analyses`; `POST /analysis/{cv_id}`, `GET /analysis/{id}`.
- `services/llm.py`: anonimisasi (nama, email, telepon, alamat, link profil, perusahaan) sebelum kirim; prompt hanya untuk saran; fallback saran berbasis aturan bila API key tidak ada/gagal.
- Frontend: tampilkan skor total + breakdown + kartu saran.

**Test**
- Satu test per kriteria (batas bawah/atas, input minimal), jumlah bobot = 100, agregasi & pembulatan.
- Anonimizer: pastikan tidak ada PII tersisa di payload (mock LLM, assert request).
- Endpoint analysis: skor dihitung kode, bukan dari respons LLM.

**Selesai bila:** skor konsisten untuk CV contoh, tiap kriteria punya alasan, dan saran muncul tanpa membocorkan PII.

---

## Fase 4 — Seed lowongan + Job Matcher (Minggu 4)

**Tujuan:** rekomendasi lowongan dengan persentase kecocokan yang bisa dijelaskan.

**Deliverable**
- `data/jobs_seed.json` 30–50 lowongan + `job_skills` (wajib/nilai tambah) + skrip seeding.
- Embedding `all-MiniLM-L6-v2` untuk ringkasan profil & deskripsi lowongan (pgvector atau kolom vektor).
- `services/matching.py`: `skill_coverage` (skill wajib berbobot lebih tinggi) dan `semantic_similarity` (cosine), `match_score = 0.6*coverage + 0.4*similarity`.
- Matched/missing skills dari operasi himpunan (tanpa LLM); model `job_matches`.
- `GET /jobs/match/{analysis_id}`.
- Frontend: halaman Job Matches (persen, skill cocok/kurang, alasan).

**Test**
- Coverage (semua/partial/tanpa skill wajib), bobot wajib vs tambahan, formula & pembulatan.
- Similarity dengan vektor stub deterministik (tanpa download model saat test).
- Endpoint: urutan hasil, isolasi data antar user.

**Selesai bila:** tiap lowongan menampilkan persen + matched/missing yang konsisten dengan data seed.

---

## Fase 5 — Dashboard, grafik, skill gap & roadmap (Minggu 5)

**Tujuan:** hasil analisis tersaji dan actionable.

**Deliverable**
- `GET /skills/gap/{analysis_id}`: skill kurang per kategori + agregasi dari lowongan teratas.
- `learning_resources` + seed tautan per skill.
- Frontend dashboard: gauge skor, bar breakdown, radar skill, kartu rekomendasi.
- Halaman Skill Gap & Roadmap (urutan prioritas belajar dari gap + resource).

**Test**
- Logika gap (deduplikasi, prioritas wajib, kategori), endpoint gap & resource, kasus tanpa gap.
- Snapshot/unit test komponen chart bila waktu memungkinkan.

**Selesai bila:** satu CV penuh menghasilkan dashboard lengkap dan roadmap yang masuk akal.

---

## Fase 6 — Testing menyeluruh, hardening, deploy, dokumentasi (Minggu 6)

**Tujuan:** MVP memenuhi definition of done §13.

**Deliverable**
- Audit semua endpoint §8 punya test; perbaikan bug; target coverage layanan inti ≥ 80%.
- `DELETE /cv/{id}` cascade penuh (file fisik, profile, skills, analyses, matches) + test privasi.
- Error handling & validasi konsisten, rate limit dasar, logging tanpa PII.
- `README.md`: cara jalan, penjelasan rubrik, screenshot, CV contoh untuk demo.
- Deploy (docker-compose produksi/VPS) + cek `docker compose up` dari nol.

**Test**
- Regresi end-to-end alur: register → upload → review → analyze → match → gap → hapus.
- Cascade deletion, akses lintas user, file rusak/oversize.

**Selesai bila:** repo bersih bisa dijalankan sekali perintah, semua test hijau, README lengkap.

---

## Ringkasan jadwal

| Fase | Minggu | Fokus |
|---|---|---|
| 1 | 1 | Fondasi, Docker, DB, auth, UI dasar |
| 2 | 2 | Parser, skill extraction, review |
| 3 | 3 | Rubrik skor + saran LLM |
| 4 | 4 | Seed lowongan + matcher |
| 5 | 5 | Dashboard, grafik, skill gap |
| 6 | 6 | Testing, hardening, deploy, README |
