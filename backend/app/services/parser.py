import io
import re
import zipfile
from dataclasses import dataclass

import pdfplumber
from docx import Document

PDF_MIME = "application/pdf"
DOCX_MIME = (
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
)
SUPPORTED_EXTENSIONS = {".pdf", ".docx"}


class ParserError(Exception):
    pass


class EmptyDocumentError(ParserError):
    pass


@dataclass(frozen=True)
class ParsedDocument:
    text: str
    page_count: int | None = None
    has_tables: bool = False
    has_images: bool = False


def normalize_text(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n").replace("\xa0", " ")
    lines = [re.sub(r"[ \t]+", " ", line).strip() for line in text.split("\n")]
    cleaned: list[str] = []
    blank = False
    for line in lines:
        if line:
            cleaned.append(line)
            blank = False
        elif not blank:
            cleaned.append("")
            blank = True
    return "\n".join(cleaned).strip()


def is_pdf_bytes(data: bytes) -> bool:
    return data[:5] == b"%PDF-"


def is_docx_bytes(data: bytes) -> bool:
    if data[:4] != b"PK\x03\x04":
        return False
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            return "word/document.xml" in archive.namelist()
    except zipfile.BadZipFile:
        return False


def parse_pdf_document(data: bytes) -> ParsedDocument:
    if not is_pdf_bytes(data):
        raise ParserError("Isi file tidak cocok dengan format PDF.")

    try:
        with pdfplumber.open(io.BytesIO(data)) as pdf:
            pages = list(pdf.pages)
            texts = [page.extract_text() or "" for page in pages]
            has_images = any(bool(page.images) for page in pages)
            has_tables = False
            for page in pages:
                try:
                    if page.find_tables():
                        has_tables = True
                except Exception:
                    continue
            page_count = len(pages)
    except ParserError:
        raise
    except Exception as exc:
        raise ParserError("File PDF rusak atau tidak dapat dibaca.") from exc

    text = normalize_text("\n".join(texts))
    if not text:
        raise EmptyDocumentError(
            "PDF tidak mengandung teks yang bisa dibaca. Kemungkinan file hasil scan; "
            "silakan unggah PDF berbasis teks atau DOCX."
        )
    return ParsedDocument(
        text=text,
        page_count=page_count,
        has_tables=has_tables,
        has_images=has_images,
    )


def parse_docx_document(data: bytes) -> ParsedDocument:
    if not is_docx_bytes(data):
        raise ParserError("Isi file tidak cocok dengan format DOCX.")

    try:
        document = Document(io.BytesIO(data))
        parts = [paragraph.text for paragraph in document.paragraphs]
        for table in document.tables:
            for row in table.rows:
                cells = [cell.text.strip() for cell in row.cells]
                unique_cells = list(dict.fromkeys(cell for cell in cells if cell))
                if unique_cells:
                    parts.append(" | ".join(unique_cells))
        has_tables = bool(document.tables)
        has_images = bool(document.inline_shapes) or any(
            "image" in relationship.reltype
            for relationship in document.part.rels.values()
        )
    except Exception as exc:
        raise ParserError("File DOCX rusak atau tidak dapat dibaca.") from exc

    text = normalize_text("\n".join(parts))
    if not text:
        raise EmptyDocumentError(
            "Dokumen Word tidak mengandung teks yang bisa dibaca."
        )
    return ParsedDocument(
        text=text,
        page_count=None,
        has_tables=has_tables,
        has_images=has_images,
    )


def parse_pdf(data: bytes) -> str:
    return parse_pdf_document(data).text


def parse_docx(data: bytes) -> str:
    return parse_docx_document(data).text


def parse_document_detailed(data: bytes, suffix: str) -> ParsedDocument:
    suffix = suffix.lower()
    if suffix == ".pdf":
        return parse_pdf_document(data)
    if suffix == ".docx":
        return parse_docx_document(data)
    raise ParserError("Format file harus PDF atau DOCX.")


def parse_document(data: bytes, suffix: str) -> str:
    return parse_document_detailed(data, suffix).text
