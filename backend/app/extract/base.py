"""The Block IR — the only thing that may cross out of app/extract/.

Every format-specific extractor exposes a module-level `extract(path)`
matching `ExtractFn`. No PyMuPDF/python-docx/python-pptx object may appear
in a caller's hands; everything is flattened to `Block` first.
"""

from collections.abc import Callable
from pathlib import Path
from typing import Literal, TypedDict


class Block(TypedDict):
    type: Literal["heading", "paragraph", "list", "table"]
    text: str
    level: int | None  # 1-6 for headings, None otherwise
    anchor: int  # page/slide number, or sequential index — internal only, never displayed


ExtractFn = Callable[[Path], list[Block]]


class ScannedDocumentError(Exception):
    """Raised when a document has near-zero extractable text — e.g. a
    scanned PDF with no OCR text layer. OCR is out of scope by design; the
    job should fail with a clear message rather than "succeed" with an
    empty document."""

