# Demo CareerLens AI

Folder ini berisi satu CV fiktif dalam format PDF dan DOCX untuk mencoba
alur aplikasi tanpa memakai data pribadi nyata.

- `cv-contoh-anonim.pdf`
- `cv-contoh-anonim.docx`

Semua data (nama, email, telepon, tautan, institusi, dan perusahaan) adalah
contoh fiktif. Domain memakai `example.com` dan nomor telepon memakai awalan
`0000` agar tidak menunjuk ke orang sungguhan.

## Langkah demo singkat

1. Jalankan seluruh stack dari akar repo:

   ```bash
   docker compose up --build
   ```

   Tunggu sampai API sehat di `http://localhost:8000/health` dan frontend
   tersedia di `http://localhost:5173`.

2. Buka frontend, pilih **Mulai gratis**, lalu daftar dengan email apa pun
   (boleh `demo@example.com`) dan password minimal 8 karakter.

3. Masuk ke **Upload CV**, unggah `cv-contoh-anonim.pdf` atau
   `cv-contoh-anonim.docx`, lalu tunggu ekstraksi selesai.

4. Di halaman **Review**, periksa hasil ekstraksi. Skill seperti Python,
   FastAPI, PostgreSQL, Docker, dan React seharusnya terdeteksi. Simpan bila
   sudah benar, lalu jalankan analisis.

5. Lihat **Dashboard**: skor total, breakdown 5 kriteria, coverage per
   kategori, top 5 lowongan, top skill gap, dan saran. Buka **Riwayat** untuk
   grafik perkembangan dan perbandingan antar analisis.

6. Buka **Roadmap** dari kartu skill gap untuk melihat urutan prioritas,
   sumber belajar, dan checkbox "sudah dipelajari".

7. Untuk menguji privasi, buka menu akun lalu **Hapus akun**. Seluruh CV,
   profil, analisis, job match, dan file fisik akan dihapus.

## Membuat ulang file demo

Dari folder `backend/` dengan virtualenv aktif:

```bash
python ../demo/generate_demo_cv.py
```

Skrip memerlukan `python-docx` dan `fpdf2` (sudah ada di
`backend/requirements.txt`).
