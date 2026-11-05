"""Small helpers for opening files and guessing their format."""
from __future__ import annotations

import gzip
from pathlib import Path
from typing import IO, Optional


def open_text(path: Path) -> IO[str]:
    """Open plain or gzip-compressed text the same way (like zcat vs cat)."""
    if str(path).endswith(".gz"):
        return gzip.open(path, "rt", encoding="utf-8", errors="replace")
    return open(path, "r", encoding="utf-8", errors="replace")


def detect_format(path: Path) -> Optional[str]:
    """Guess the file type from its extension. Returns 'vcf', 'fastq', or None."""
    name = path.name.lower()
    if name.endswith(".gz"):
        name = name[:-3]
    if name.endswith(".vcf"):
        return "vcf"
    if name.endswith((".fastq", ".fq")):
        return "fastq"
    return None
