"""Turn a list of findings into output for humans (text) or programs (JSON)."""
from __future__ import annotations

import json
from collections import Counter
from typing import List

from genoscan import __version__
from genoscan.findings import Finding, Severity


def sort_findings(findings: List[Finding]) -> List[Finding]:
    """Group by file, most severe first, then by line number."""
    return sorted(findings, key=lambda f: (f.file, -f.severity, f.line or 0))


def summary(findings: List[Finding]) -> dict:
    counts = Counter(f.severity.name for f in findings)
    return {s.name.lower(): counts.get(s.name, 0) for s in sorted(Severity, reverse=True)}


def to_text(findings: List[Finding], files_scanned: int) -> str:
    lines: List[str] = []
    current_file = None
    for f in sort_findings(findings):
        if f.file != current_file:
            if current_file is not None:
                lines.append("")
            lines.append(f.file)
            current_file = f.file
        where = f"line {f.line}" if f.line else ""
        lines.append(f"  {f.severity.name:<7} {where:<10} {f.rule}: {f.message}")
        lines.append(f"  {'':<7} {'':<10} evidence: {f.evidence}")

    counts = summary(findings)
    if findings:
        lines.append("")
    lines.append(
        f"Scanned {files_scanned} file(s): "
        f"{counts['high']} high, {counts['medium']} medium, {counts['low']} low"
    )
    return "\n".join(lines)


def to_json(findings: List[Finding], files_scanned: int) -> str:
    return json.dumps(
        {
            "tool": "genoscan",
            "version": __version__,
            "files_scanned": files_scanned,
            "summary": summary(findings),
            "findings": [f.to_dict() for f in sort_findings(findings)],
        },
        indent=2,
    )
