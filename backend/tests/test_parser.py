from pathlib import Path

import pytest

from app.services.parser import (
    DOCX_MIME,
    EmptyDocumentError,
    ParserError,
    parse_document,
    parse_document_detailed,
    parse_docx,
    parse_pdf,
)

FIXTURES = Path(__file__).resolve().parent / "fixtures"


def read_fixture(name: str) -> bytes:
    return (FIXTURES / name).read_bytes()


@pytest.mark.parametrize(
    "filename",
    [
        "indonesian.pdf",
        "indonesian.docx",
        "english.pdf",
        "english.docx",
        "messy.pdf",
        "messy.docx",
    ],
)
def test_parse_fixtures_returns_text(filename):
    text = parse_document(read_fixture(filename), Path(filename).suffix)

    assert len(text) > 100
    assert "@" in text
    assert "Python" in text or "SITI" in text


def test_scanned_pdf_raises_friendly_error():
    with pytest.raises(EmptyDocumentError) as error:
        parse_pdf(read_fixture("scanned.pdf"))

    message = str(error.value).lower()
    assert "scan" in message
    assert "docx" in message


def test_corrupt_pdf_raises_parser_error():
    with pytest.raises(ParserError):
        parse_pdf(b"%PDF-1.4\nini bukan struktur pdf yang valid")


def test_pdf_with_wrong_magic_is_rejected():
    with pytest.raises(ParserError):
        parse_pdf(b"bukan file pdf sama sekali")


def test_docx_with_wrong_magic_is_rejected():
    with pytest.raises(ParserError):
        parse_docx(b"bukan file docx")


def test_unsupported_extension_is_rejected():
    with pytest.raises(ParserError):
        parse_document(b"data", ".txt")


def test_docx_parses_table_content():
    text = parse_document(read_fixture("messy.docx"), ".docx")

    assert "Google Data Analytics" in text


def test_docx_mime_constant_matches_spec():
    assert DOCX_MIME == (
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )


def test_pdf_metadata_includes_page_count():
    parsed = parse_document_detailed(read_fixture("indonesian.pdf"), ".pdf")

    assert parsed.text
    assert parsed.page_count == 1
    assert parsed.has_tables is False


def test_docx_metadata_detects_tables_without_page_count():
    parsed = parse_document_detailed(read_fixture("messy.docx"), ".docx")

    assert parsed.page_count is None
    assert parsed.has_tables is True
