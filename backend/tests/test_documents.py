import io
import zipfile

import pytest

from app.services.documents import (
    MAX_FILE_BYTES,
    DocumentTooLong,
    FileTooLarge,
    UnreadableDocument,
    UnsupportedFile,
    detect_kind,
    extract_text,
)
from tests.factories import CV_DOCX, CV_PDF, LINKEDIN_PDF, make_docx, make_pdf


def test_reads_pdf() -> None:
    text = extract_text(CV_PDF)
    assert "Laura Gomez Ruiz" in text
    assert "Acme Logistics" in text


def test_reads_docx_including_tables() -> None:
    assert "FastAPI" in extract_text(CV_DOCX)


def test_reads_linkedin_pdf() -> None:
    assert "Aptitudes principales" in extract_text(LINKEDIN_PDF)


def test_file_type_comes_from_bytes_not_name() -> None:
    with pytest.raises(UnsupportedFile):
        detect_kind(b"just some text pretending to be a CV")
    with pytest.raises(UnsupportedFile):
        detect_kind(b"PK\x03\x04 not really a zip")
    # A valid zip that is not a Word document.
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("hello.txt", "hi")
    with pytest.raises(UnsupportedFile):
        detect_kind(buf.getvalue())


def test_rejects_too_large() -> None:
    with pytest.raises(FileTooLarge):
        extract_text(b"%PDF-" + b"0" * MAX_FILE_BYTES)


def test_rejects_documents_without_text() -> None:
    with pytest.raises(UnreadableDocument):
        extract_text(make_pdf(["short"]))


def test_rejects_damaged_pdf() -> None:
    with pytest.raises(UnreadableDocument):
        extract_text(b"%PDF-1.4\n garbage garbage")


def test_never_truncates_long_documents() -> None:
    with pytest.raises(DocumentTooLong):
        extract_text(make_docx(["x" * 1000] * 70))


def test_rejects_zip_bombs() -> None:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("word/document.xml", "<w/>")
        zf.writestr("word/padding.bin", b"\0" * (30 * 1024 * 1024))  # compresses to ~30 KB
    data = buf.getvalue()
    assert len(data) < MAX_FILE_BYTES
    with pytest.raises(UnsupportedFile):
        extract_text(data)
