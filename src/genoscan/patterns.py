"""Generic patterns that mean trouble in ANY text-based genomic file.

If you know `grep -E`, these are the same idea: each Pattern is a regex plus
a severity and an explanation. Format-specific checks live in scanners/.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Callable, List, Optional

from genoscan.findings import Severity


@dataclass(frozen=True)
class Pattern:
    rule: str
    severity: Severity
    regex: "re.Pattern[str]"
    message: str
    # Optional extra check to cut false positives. Gets the match and the line.
    validate: Optional[Callable[["re.Match[str]", str], bool]] = None


def _looks_like_ip(match: "re.Match[str]", line: str) -> bool:
    """Reject things like 'version=4.2.6.1' that look like IPs but aren't."""
    octets = [int(part) for part in match.group(0).split(".")]
    if any(o > 255 for o in octets):
        return False
    before = line[max(0, match.start() - 12):match.start()].lower()
    if "version" in before or before.endswith("v"):
        return False
    return True


GENERIC_PATTERNS: List[Pattern] = [
    Pattern(
        rule="home-directory",
        severity=Severity.HIGH,
        regex=re.compile(r"(?:/home/|/Users/|[A-Za-z]:\\Users\\)[A-Za-z0-9._-]+"),
        message="Home directory path reveals a username",
    ),
    Pattern(
        rule="email",
        severity=Severity.HIGH,
        regex=re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"),
        message="Email address",
    ),
    Pattern(
        rule="ip-address",
        severity=Severity.MEDIUM,
        regex=re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b"),
        message="IP address can reveal internal servers or network layout",
        validate=_looks_like_ip,
    ),
    Pattern(
        rule="absolute-path",
        severity=Severity.MEDIUM,
        regex=re.compile(r"(?:file://)?/(?:[A-Za-z0-9._-]+/){2,}[A-Za-z0-9._-]*"),
        message="Absolute file path can reveal server layout, project or lab names",
    ),
]


@dataclass(frozen=True)
class Match:
    pattern: Pattern
    start: int
    end: int
    text: str


def scan_text(line: str, patterns: List[Pattern] = GENERIC_PATTERNS) -> List[Match]:
    """Return every pattern hit in one line of text.

    When two hits overlap (e.g. '/Users/jdoe/data/x.vcf' is both a home
    directory AND an absolute path) we keep only the more severe one, so the
    report isn't full of duplicates.
    """
    hits: List[Match] = []
    for pattern in patterns:
        for m in pattern.regex.finditer(line):
            if pattern.validate and not pattern.validate(m, line):
                continue
            hits.append(Match(pattern, m.start(), m.end(), m.group(0)))

    # Most severe first, then keep a hit only if it doesn't overlap a kept one.
    hits.sort(key=lambda h: -h.pattern.severity)
    kept: List[Match] = []
    for hit in hits:
        if all(hit.end <= k.start or hit.start >= k.end for k in kept):
            kept.append(hit)
    return sorted(kept, key=lambda h: h.start)
