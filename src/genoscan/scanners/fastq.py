"""Scanner for FASTQ (sequencing reads) files.

Every read is 4 lines:
  @read_name optional_comment
  ACGT...            (the sequence)
  +                  (separator, sometimes repeats the name)
  IIII...            (quality scores)

Illumina read names usually look like:
  @INSTRUMENT:RUN:FLOWCELL:LANE:TILE:X:Y READ:FILTERED:CONTROL:INDEX

The instrument serial and flowcell ID tie a file to one machine and one
sequencing run, which can be traced back to a facility (and its records).
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, List, Tuple

from genoscan.fileio import open_text
from genoscan.findings import Finding, Severity
from genoscan.patterns import scan_text

# Reading every record of a 50 GB file is slow and repetitive; the identifying
# parts repeat in every read, so a sample from the start is enough.
DEFAULT_MAX_RECORDS = 10_000

ILLUMINA_NAME = re.compile(
    r"^@(?P<instrument>[A-Za-z0-9_-]+):(?P<run>\d+):(?P<flowcell>[A-Za-z0-9-]+)"
    r":(?P<lane>\d+):(?P<tile>\d+):(?P<x>\d+):(?P<y>\d+)"
    r"(?:\s+[12]:[YN]:\d+:(?P<index>[ACGTN]+(?:\+[ACGTN]+)?))?"
)


def scan_fastq(path: Path, max_records: int = DEFAULT_MAX_RECORDS) -> List[Finding]:
    # Only report each unique value once: {(rule, evidence): first line number}
    first_seen: Dict[Tuple[str, str], Tuple[int, Severity, str]] = {}

    def note(rule: str, evidence: str, lineno: int, severity: Severity, message: str) -> None:
        first_seen.setdefault((rule, evidence), (lineno, severity, message))

    with open_text(path) as fh:
        for lineno, raw in enumerate(fh, start=1):
            position = (lineno - 1) % 4          # 0=name, 1=seq, 2=+, 3=quality
            record_number = (lineno - 1) // 4
            if record_number >= max_records:
                break
            if position not in (0, 2):
                continue                          # sequence/quality: nothing to leak

            line = raw.rstrip("\r\n")
            if position == 0:
                m = ILLUMINA_NAME.match(line)
                if m:
                    note("fastq-instrument", m.group("instrument"), lineno, Severity.MEDIUM,
                         "Instrument serial number identifies the sequencing machine "
                         "(and usually the facility)")
                    note("fastq-flowcell", f"{m.group('flowcell')} (run {m.group('run')})",
                         lineno, Severity.MEDIUM,
                         "Flowcell and run IDs link these reads to one specific sequencing run")
                    if m.group("index"):
                        note("fastq-index", m.group("index"), lineno, Severity.LOW,
                             "Sample barcode can link this file to others from the same library")

            for hit in scan_text(line):
                note(hit.pattern.rule, hit.text, lineno,
                     hit.pattern.severity, hit.pattern.message)

    return [
        Finding(str(path), lineno, severity, rule, message, evidence)
        for (rule, evidence), (lineno, severity, message) in first_seen.items()
    ]
