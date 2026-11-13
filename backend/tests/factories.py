"""Builders for synthetic (fully invented, anonymised) CV documents used in tests."""

import io

from docx import Document

CV_LINES = [
    "Laura Gomez Ruiz",
    "Backend Developer",
    "Madrid, Spain | laura.dev@example.com | github.com/laura-dev",
    "EXPERIENCE",
    "Senior Backend Developer - Acme Logistics (2021-03 - Present)",
    "Designed REST APIs with Python and FastAPI; migrated services to PostgreSQL.",
    "Backend Developer - Nimbus Apps (2018-06 - 2021-02)",
    "Built microservices with Django and Docker.",
    "EDUCATION",
    "Grado en Ingenieria Informatica - Universidad de Sevilla (2014 - 2018)",
    "SKILLS: Python, FastAPI, Django, PostgreSQL, Docker, Git",
    "LANGUAGES: Spanish (Native), English (C1)",
]

LINKEDIN_LINES = [
    "Contactar",
    "www.linkedin.com/in/laura-dev",
    "Aptitudes principales",
    "Python",
    "FastAPI",
    "Languages",
    "English (Full Professional)",
    "Laura Gomez Ruiz",
    "Backend Developer en Acme Logistics",
    "Experiencia",
    "Acme Logistics",
    "Senior Backend Developer",
    "marzo de 2021 - Present",
    "Page 1 of 1",
]


def _pdf_escape(text: str) -> str:
    return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def make_pdf(lines: list[str]) -> bytes:
    """Minimal valid single-page PDF with real text (Helvetica), readable by pypdf."""
    content_lines = ["BT", "/F1 10 Tf", "40 800 Td", "14 TL"]
    for line in lines:
        content_lines.append(f"({_pdf_escape(line)}) Tj T*")
    content_lines.append("ET")
    stream = "\n".join(content_lines).encode("latin-1")

    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] "
        b"/Resources << /Font << /F1 5 0 R >> >> /Contents 4 0 R >>",
        b"<< /Length " + str(len(stream)).encode() + b" >>\nstream\n" + stream + b"\nendstream",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]
    out = io.BytesIO()
    out.write(b"%PDF-1.4\n")
    offsets = []
    for number, body in enumerate(objects, start=1):
        offsets.append(out.tell())
        out.write(f"{number} 0 obj\n".encode() + body + b"\nendobj\n")
    xref = out.tell()
    out.write(f"xref\n0 {len(objects) + 1}\n0000000000 65535 f \n".encode())
    for off in offsets:
        out.write(f"{off:010d} 00000 n \n".encode())
    out.write(
        f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode()
    )
    return out.getvalue()


def make_docx(lines: list[str]) -> bytes:
    doc = Document()
    for line in lines:
        doc.add_paragraph(line)
    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()


CV_PDF = make_pdf(CV_LINES)
CV_DOCX = make_docx(CV_LINES)
LINKEDIN_PDF = make_pdf(LINKEDIN_LINES)
CV_TEXT = "\n".join(CV_LINES)
