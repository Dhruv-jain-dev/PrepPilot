from __future__ import annotations

from io import BytesIO

from pypdf import PdfReader


def extract_pdf_text(content: bytes) -> str:
    try:
        reader = PdfReader(BytesIO(content))
    except Exception as exc:
        raise ValueError("The uploaded file is not a readable PDF.") from exc
    text = "\n\n".join((page.extract_text() or "").strip() for page in reader.pages).strip()
    if not text:
        raise ValueError("No selectable text was found in the PDF. Upload a text-based PDF.")
    return text
