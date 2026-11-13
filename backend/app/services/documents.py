"""Safe text extraction from uploaded CVs (PDF / DOCX).

Security (docs/seguridad.md): the real file type is detected from its bytes (never from the
name or the client's Content-Type), size and page counts are capped, and DOCX archives are
checked for zip bombs before parsing. Files are processed in memory and never written to disk.
"""

import io
import re
import zipfile

from docx import Document
from pypdf import PdfReader
from pypdf.errors import PdfReadError

from app.core.errors import AppError

MAX_FILE_BYTES = 5 * 1024 * 1024
MAX_PDF_PAGES = 20
MAX_DOCX_UNCOMPRESSED = 25 * 1024 * 1024
MAX_TEXT_CHARS = 60_000
MIN_TEXT_CHARS = 80


class UnsupportedFile(AppError):
    status_code, code, message = 415, "unsupported_file", "Only PDF and DOCX files are accepted."


class FileTooLarge(AppError):
    status_code, code, message = 413, "file_too_large", "The file exceeds 5 MB."


class UnreadableDocument(AppError):
    status_code, code = 422, "cv_unreadable"
    message = "No text could be read from the file (is it a scanned image?)."


class DocumentTooLong(AppError):
    status_code, code, message = 422, "cv_too_long", "The document is too long for a CV."


def detect_kind(data: bytes) -> str:
    if data.startswith(b"%PDF-"):
        return "pdf"
    if data.startswith(b"PK\x03\x04"):
        try:
            with zipfile.ZipFile(io.BytesIO(data)) as zf:
                if "word/document.xml" in zf.namelist():
                    return "docx"
        except zipfile.BadZipFile:
            pass
    raise UnsupportedFile()


def _pdf_text(data: bytes) -> str:
    try:
        reader = PdfReader(io.BytesIO(data))
        if reader.is_encrypted:
            raise UnreadableDocument("The PDF is password protected.")
        if len(reader.pages) > MAX_PDF_PAGES:
            raise DocumentTooLong(f"The PDF has more than {MAX_PDF_PAGES} pages.")
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    except PdfReadError as exc:
        raise UnreadableDocument("The PDF file is damaged.") from exc


def _docx_text(data: bytes) -> str:
    with zipfile.ZipFile(io.BytesIO(data)) as zf:
        if sum(i.file_size for i in zf.infolist()) > MAX_DOCX_UNCOMPRESSED:
            raise UnsupportedFile("The DOCX file is suspiciously large once decompressed.")
    try:
        doc = Document(io.BytesIO(data))
    except Exception as exc:  # python-docx raises several unrelated types
        raise UnreadableDocument("The DOCX file is damaged.") from exc
    parts = [p.text for p in doc.paragraphs]
    for table in doc.tables:
        for row in table.rows:
            parts.append(" | ".join(cell.text for cell in row.cells))
    return "\n".join(parts)


def normalize_text(text: str) -> str:
    text = text.replace("\x00", "")
    text = re.sub(r"[ \t\xa0]+", " ", text)  # \xa0 = non-breaking space
    text = re.sub(r"\n\s*\n\s*\n+", "\n\n", text)
    return text.strip()


def extract_text(data: bytes) -> str:
    """Return clean plain text from a PDF/DOCX, or raise a user-facing AppError."""
    if len(data) > MAX_FILE_BYTES:
        raise FileTooLarge()
    kind = detect_kind(data)
    raw = _pdf_text(data) if kind == "pdf" else _docx_text(data)
    text = normalize_text(raw)
    if len(text) < MIN_TEXT_CHARS:
        raise UnreadableDocument()
    if len(text) > MAX_TEXT_CHARS:
        # Never truncate silently: a partial CV would produce a misleading profile.
        raise DocumentTooLong()
    return text
