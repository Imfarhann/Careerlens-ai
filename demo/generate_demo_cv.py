from pathlib import Path

from docx import Document
from fpdf import FPDF

DEMO_DIR = Path(__file__).resolve().parent

CONTENT = """KANDIDAT CONTOH
kandidat.contoh@example.com | +62 812-0000-0000
GitHub: https://github.com/contoh-kandidat
LinkedIn: linkedin.com/in/contoh-kandidat

RINGKASAN
Backend engineer dengan 4 tahun pengalaman membangun API menggunakan Python dan FastAPI.
Terbiasa bekerja dengan PostgreSQL, Docker, dan pipeline CI/CD sederhana.

PENDIDIKAN
Universitas Contoh
S1 Ilmu Komputer
2016 - 2020

PENGALAMAN KERJA
Backend Engineer
PT Contoh Teknologi
2021 - Sekarang
- Membangun REST API dengan Python, FastAPI, PostgreSQL, dan Docker
- Meningkatkan performa query hingga 40 persen melalui indeks dan caching
- Mengotomatiskan deployment dengan GitHub Actions dan Docker Compose
- Menulis unit test dengan pytest untuk menjaga kualitas layanan

PROYEK
CareerLens Demo API
2023
- Membangun layanan analisis CV dengan FastAPI dan PostgreSQL
- Menerapkan pencocokan skill berbasis himpunan dan embedding kalimat
- Menyediakan dashboard berisi skor, skill gap, dan rekomendasi lowongan

KEAHLIAN
Python, FastAPI, PostgreSQL, Docker, Git, AWS, React, SQL, Komunikasi, Analisis Data"""


def write_pdf(path: Path, content: str) -> None:
    pdf = FPDF()
    pdf.set_margins(15, 15, 15)
    pdf.add_page()
    pdf.set_font("Helvetica", size=10)
    for line in content.split("\n"):
        pdf.multi_cell(0, 6, line, new_x="LMARGIN", new_y="NEXT")
    pdf.output(str(path))


def write_docx(path: Path, content: str) -> None:
    document = Document()
    for line in content.split("\n"):
        document.add_paragraph(line)
    document.save(str(path))


def main() -> None:
    write_pdf(DEMO_DIR / "cv-contoh-anonim.pdf", CONTENT)
    write_docx(DEMO_DIR / "cv-contoh-anonim.docx", CONTENT)
    print("Demo CV dibuat: cv-contoh-anonim.pdf dan cv-contoh-anonim.docx")


if __name__ == "__main__":
    main()
