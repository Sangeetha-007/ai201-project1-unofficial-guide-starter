"""Milestone 3 — Document ingestion and chunking.

Loads every document in documents/, cleans the raw text, and splits it into
overlapping chunks sized for the all-MiniLM-L6-v2 embedding model.

Chunking strategy (see planning.md):
    Chunk size = 128 tokens
    Overlap    = 13 tokens (~10% of chunk size)

Token counts are measured with the same tokenizer the embedding model uses, so
a "128-token chunk" here is exactly what the embedder will see at retrieval time
(all-MiniLM-L6-v2 has a 256-token window, so 128 leaves comfortable headroom).

Output: data/chunks.json — a list of {id, source, chunk_index, token_count, text}.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from transformers import AutoTokenizer

# --- Configuration -----------------------------------------------------------

EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
CHUNK_SIZE = 128          # tokens per chunk
OVERLAP = 13              # tokens shared between consecutive chunks

REPO_ROOT = Path(__file__).resolve().parent.parent
DOCUMENTS_DIR = REPO_ROOT / "documents"
OUTPUT_PATH = REPO_ROOT / "data" / "chunks.json"


# --- Loading -----------------------------------------------------------------

def load_txt(path: Path) -> str:
    """Read a plain-text document."""
    return path.read_text(encoding="utf-8", errors="ignore")


def load_pdf(path: Path) -> str:
    """Extract text from a PDF, one page after another."""
    import pdfplumber  # imported lazily so .txt-only runs don't need it

    pages = []
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            pages.append(page.extract_text() or "")
    return "\n".join(pages)


def load_docx(path: Path) -> str:
    """Extract text from a Word document, one paragraph per line."""
    import docx  # python-docx; imported lazily

    document = docx.Document(path)
    return "\n".join(p.text for p in document.paragraphs)


LOADERS = {".txt": load_txt, ".pdf": load_pdf, ".docx": load_docx}


# --- Cleaning ----------------------------------------------------------------

def clean_text(text: str) -> str:
    """Normalize whitespace and strip artifacts left by scraping / PDF extraction.

    - Collapses runs of spaces/tabs into a single space.
    - Collapses 3+ blank lines into a single blank line (keeps paragraph breaks).
    - Drops lone "*" lines and other stray separator characters that appear at
      the end of the scraped RateMyProfessor files.
    """
    # Normalize line endings.
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    cleaned_lines = []
    for line in text.split("\n"):
        line = re.sub(r"[ \t]+", " ", line).strip()
        # Skip lines that are only separator punctuation (e.g. a trailing "*").
        if line and not re.fullmatch(r"[*_=\-]+", line):
            cleaned_lines.append(line)
        else:
            cleaned_lines.append("")  # preserve as a blank line / paragraph break

    text = "\n".join(cleaned_lines)
    # Collapse 3+ newlines into a paragraph break, then trim.
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


# --- Chunking ----------------------------------------------------------------

def chunk_text(text: str, tokenizer, chunk_size: int = CHUNK_SIZE,
               overlap: int = OVERLAP) -> list[str]:
    """Split text into overlapping chunks of `chunk_size` tokens.

    Consecutive chunks share `overlap` tokens so a fact that lands near a
    boundary still appears intact in at least one chunk. The chunk window
    advances by (chunk_size - overlap) tokens each step.

    Size is measured with the embedding model's tokenizer, but each chunk is
    sliced out of the ORIGINAL text using token->character offsets. That keeps
    the real casing and punctuation (e.g. "3.7", "CISC 3150") instead of the
    lowercased, space-padded form you'd get from decoding token ids.
    """
    if overlap >= chunk_size:
        raise ValueError("overlap must be smaller than chunk_size")

    encoding = tokenizer(text, add_special_tokens=False,
                         return_offsets_mapping=True)
    offsets = encoding["offset_mapping"]
    if not offsets:
        return []

    step = chunk_size - overlap
    chunks = []
    for start in range(0, len(offsets), step):
        window = offsets[start:start + chunk_size]
        char_start = window[0][0]
        char_end = window[-1][1]
        chunk = text[char_start:char_end].strip()
        if chunk:
            chunks.append(chunk)
        if start + chunk_size >= len(offsets):
            break  # last window already reached the end
    return chunks


# --- Pipeline ----------------------------------------------------------------

def ingest() -> list[dict]:
    """Load, clean, and chunk every supported document in documents/."""
    print(f"Loading tokenizer for {EMBEDDING_MODEL} ...")
    tokenizer = AutoTokenizer.from_pretrained(EMBEDDING_MODEL)

    records: list[dict] = []
    files = sorted(p for p in DOCUMENTS_DIR.iterdir()
                   if p.suffix.lower() in LOADERS)

    if not files:
        raise SystemExit(f"No .txt or .pdf documents found in {DOCUMENTS_DIR}")

    for path in files:
        raw = LOADERS[path.suffix.lower()](path)
        cleaned = clean_text(raw)
        chunks = chunk_text(cleaned, tokenizer)
        print(f"  {path.name:25s} -> {len(chunks):3d} chunks")

        for i, chunk in enumerate(chunks):
            records.append({
                "id": f"{path.stem}-{i}",
                "source": path.name,
                "chunk_index": i,
                "token_count": len(tokenizer.encode(chunk, add_special_tokens=False)),
                "text": chunk,
            })

    return records


def main() -> None:
    records = ingest()
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(records, indent=2, ensure_ascii=False),
                           encoding="utf-8")
    print(f"\nWrote {len(records)} chunks from documents/ to "
          f"{OUTPUT_PATH.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()
