"""Shared test helpers. pytest loads this file automatically."""
import gzip

import pytest


@pytest.fixture
def write_file(tmp_path):
    """Write text to a temporary file and return its path (gzips if name ends in .gz)."""
    def _write(name: str, text: str):
        path = tmp_path / name
        if name.endswith(".gz"):
            with gzip.open(path, "wt") as fh:
                fh.write(text)
        else:
            path.write_text(text)
        return path
    return _write
