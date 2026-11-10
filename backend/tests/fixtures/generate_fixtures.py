from pathlib import Path

from docx import Document
from fpdf import FPDF

FIXTURES = Path(__file__).resolve().parent

INDONESIAN = """RIZKY PRATAMA
rizky.pratama@example.com | +62 812-3456-7890
GitHub: https://github.com/rizkypratama
LinkedIn: linkedin.com/in/rizkypratama

RINGKASAN
Backend engineer dengan 4 tahun pengalaman membangun API menggunakan Python dan FastAPI.

PENDIDIKAN
Universitas Indonesia
S1 Ilmu Komputer
2016 - 2020

PENGALAMAN KERJA
Backend Engineer
PT Teknologi Nusantara
2021 - Sekarang
- Membangun REST API dengan Python, FastAPI, dan PostgreSQL
- Meningkatkan performa query hingga 40 persen
- Menulis unit test dengan pytest dan Docker

PROYEK
CareerLens API
2023
- Aplikasi analisis CV dengan FastAPI, Docker, dan PostgreSQL

KEAHLIAN
Python, FastAPI, PostgreSQL, Docker, Git, AWS, Komunikasi"""

ENGLISH = """ALEX MORGAN
alex.morgan@example.com | +1 (415) 555-0132
github.com/alexmorgan | linkedin.com/in/alexmorgan

SUMMARY
Full-stack developer with 5 years of experience building web applications and data pipelines.

EDUCATION
University of California, Berkeley
B.S. Computer Science
2015 - 2019

EXPERIENCE
Software Engineer
Acme Corp
2019 - Present
- Built React and TypeScript frontends for internal analytics tools
- Deployed services on AWS using Docker and Kubernetes
- Automated CI/CD pipelines with GitHub Actions

PROJECTS
OpenBoard
2022
- Real-time collaboration board built with Node.js, React, and PostgreSQL

SKILLS
JavaScript, TypeScript, React, Node.js, Python, PostgreSQL, Docker, Kubernetes, AWS, Git, Teamwork"""

MESSY = """SITI NURHALIZA
siti.nurhaliza@example.com|081298765432|github.com/sitinurhaliza
PENGALAMAN KERJA: Staf Data Analyst di CV Maju Jaya 2022-sekarang; magang Data Analyst di PT Data Cerdas 2021-2022.
PENDIDIKAN: Universitas Brawijaya, Sarjana Statistika, 2018-2022.
KEAHLIAN: Excel, SQL, Python, Power BI, Tableau, komunikasi
PROYEK: Dashboard Penjualan (2023) menggunakan Python dan Power BI"""


def write_pdf(path: Path, content: str) -> None:
    pdf = FPDF()
    pdf.set_margins(15, 15, 15)
    pdf.add_page()
    pdf.set_font("Helvetica", size=10)
    for line in content.split("\n"):
        pdf.multi_cell(0, 6, line, new_x="LMARGIN", new_y="NEXT")
    pdf.output(str(path))


def write_docx(path: Path, content: str, with_table: bool = False) -> None:
    document = Document()
    for line in content.split("\n"):
        document.add_paragraph(line)
    if with_table:
        table = document.add_table(rows=1, cols=2)
        table.rows[0].cells[0].text = "SERTIFIKASI"
        table.rows[0].cells[1].text = "Google Data Analytics"
    document.save(str(path))


def main() -> None:
    write_pdf(FIXTURES / "indonesian.pdf", INDONESIAN)
    write_docx(FIXTURES / "indonesian.docx", INDONESIAN)
    write_pdf(FIXTURES / "english.pdf", ENGLISH)
    write_docx(FIXTURES / "english.docx", ENGLISH)
    write_pdf(FIXTURES / "messy.pdf", MESSY)
    write_docx(FIXTURES / "messy.docx", MESSY, with_table=True)

    scanned = FPDF()
    scanned.add_page()
    scanned.output(str(FIXTURES / "scanned.pdf"))


if __name__ == "__main__":
    main()
