import pdfplumber
import io


def extract_text(file_bytes: bytes) -> str:
    """Extract plain text from a PDF given its raw bytes."""
    text_parts = []
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                text_parts.append(text)
    return "\n".join(text_parts).strip()
