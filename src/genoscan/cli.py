"""Command-line interface: `genoscan scan FILE [FILE ...]`.

Exit codes follow the grep / security-scanner convention, so the tool can be
used in scripts, CI and pre-commit hooks:
  0  nothing at or above the --fail-on severity was found
  1  findings at or above --fail-on were found
  2  an error happened (missing file, unsupported format, ...)
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import List, Optional

from genoscan import __version__
from genoscan.fileio import detect_format
from genoscan.findings import Finding, Severity
from genoscan.report import to_json, to_text
from genoscan.scanners import SCANNERS

EXIT_CLEAN, EXIT_FINDINGS, EXIT_ERROR = 0, 1, 2


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="genoscan",
        description="Find identifying metadata in genomic files before you share them.",
    )
    parser.add_argument("--version", action="version", version=f"genoscan {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    scan = sub.add_parser("scan", help="scan VCF and FASTQ files (plain or .gz)")
    scan.add_argument("files", nargs="+", type=Path, help="files to scan")
    scan.add_argument("--format", choices=["text", "json"], default="text",
                      help="output format (default: text)")
    scan.add_argument("--fail-on", choices=["low", "medium", "high"], default="high",
                      help="exit with code 1 if anything this severe or worse is found "
                           "(default: high)")
    scan.add_argument("--min-severity", choices=["low", "medium", "high"], default="low",
                      help="hide findings below this severity (default: low = show all)")
    return parser


def run_scan(args: argparse.Namespace) -> int:
    findings: List[Finding] = []
    files_scanned = 0
    had_error = False

    for path in args.files:
        if not path.is_file():
            print(f"genoscan: {path}: no such file", file=sys.stderr)
            had_error = True
            continue
        fmt = detect_format(path)
        if fmt is None:
            print(f"genoscan: {path}: unsupported file type (expected .vcf, .fastq, .fq, "
                  f"optionally .gz)", file=sys.stderr)
            had_error = True
            continue
        findings.extend(SCANNERS[fmt](path))
        files_scanned += 1

    min_severity = Severity.from_name(args.min_severity)
    shown = [f for f in findings if f.severity >= min_severity]

    output = to_json(shown, files_scanned) if args.format == "json" else to_text(shown, files_scanned)
    print(output)

    if had_error:
        return EXIT_ERROR
    fail_on = Severity.from_name(args.fail_on)
    return EXIT_FINDINGS if any(f.severity >= fail_on for f in findings) else EXIT_CLEAN


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "scan":
        return run_scan(args)
    return EXIT_ERROR


if __name__ == "__main__":
    sys.exit(main())
