"""Scanner for VCF (Variant Call Format) files.

A VCF has three parts:
  ##key=value      meta-information lines (tools, dates, reference, commands)
  #CHROM ...       one header line; columns after FORMAT are sample IDs
  chr1  12345 ...  one line per variant

v0.1 checks the first two parts. Variant-level risk (rare variants that could
single someone out) is planned for v0.3.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import List, Tuple

from genoscan.fileio import open_text
from genoscan.findings import Finding, Severity
from genoscan.patterns import scan_text

# The #CHROM line has 9 fixed columns before the sample columns begin.
FIXED_COLUMNS = 9

COMMAND_KEY = re.compile(r"^##(\w*[Cc]ommand(?:[Ll]ine)?\w*)=")
SAMPLE_META = re.compile(r"^##SAMPLE=<.*?\bID=([^,>]+)")

# Patterns for judging a single sample ID.
PUBLIC_REFERENCE_ID = re.compile(r"^(?:NA|HG)\d{5}$")   # 1000 Genomes samples
DATE_IN_ID = re.compile(r"(?:19|20)\d{2}[-_/.]?(?:0[1-9]|1[0-2])[-_/.]?(?:0[1-9]|[12]\d|3[01])")
LONG_NUMBER = re.compile(r"\d{7,}")
PERSON_NAME = re.compile(r"^[A-Z][a-z]+[_\- .][A-Z][a-z]+")


def classify_sample_id(sample: str) -> Tuple[Severity, str, str]:
    """Decide how risky one sample ID looks. Returns (severity, rule, message)."""
    if PUBLIC_REFERENCE_ID.match(sample):
        return (Severity.LOW, "sample-id-public",
                "Public reference sample (e.g. 1000 Genomes); usually safe to share")
    if DATE_IN_ID.search(sample):
        return (Severity.HIGH, "sample-id-date",
                "Sample ID contains a date (possible date of birth or collection date)")
    if LONG_NUMBER.search(sample):
        return (Severity.HIGH, "sample-id-number",
                "Sample ID contains a long number (possible medical record or patient ID)")
    if PERSON_NAME.match(sample):
        return (Severity.HIGH, "sample-id-name",
                "Sample ID looks like a person's name")
    return (Severity.MEDIUM, "sample-id",
            "Sample identifier present; confirm it can't be linked back to a person")


def _scan_meta_line(path: Path, lineno: int, line: str) -> List[Finding]:
    findings: List[Finding] = []

    if line.startswith("##fileDate="):
        findings.append(Finding(str(path), lineno, Severity.LOW, "vcf-file-date",
                                "File creation date", line[len("##fileDate="):]))

    command = COMMAND_KEY.match(line)
    if command:
        findings.append(Finding(str(path), lineno, Severity.LOW, "vcf-command-line",
                                "Records the exact command that made this file; "
                                "may expose paths, sample names or internal tools",
                                command.group(1)))

    sample = SAMPLE_META.match(line)
    if sample:
        findings.append(_sample_finding(path, lineno, sample.group(1)))

    for hit in scan_text(line):
        findings.append(Finding(str(path), lineno, hit.pattern.severity,
                                hit.pattern.rule, hit.pattern.message, hit.text))
    return findings


def _sample_finding(path: Path, lineno: int, sample: str) -> Finding:
    severity, rule, message = classify_sample_id(sample)
    return Finding(str(path), lineno, severity, rule, message, sample)


def scan_vcf(path: Path) -> List[Finding]:
    findings: List[Finding] = []
    seen_samples = set()

    with open_text(path) as fh:
        for lineno, raw in enumerate(fh, start=1):
            line = raw.rstrip("\r\n")
            if line.startswith("##"):
                for f in _scan_meta_line(path, lineno, line):
                    if f.rule.startswith("sample-id"):
                        seen_samples.add(f.evidence)
                    findings.append(f)
            elif line.startswith("#CHROM"):
                for sample in line.split("\t")[FIXED_COLUMNS:]:
                    if sample and sample not in seen_samples:
                        findings.append(_sample_finding(path, lineno, sample))
                        seen_samples.add(sample)
                break  # header is done; variant records come in v0.3
            else:
                break  # not a valid header line; stop rather than guess
    return findings
