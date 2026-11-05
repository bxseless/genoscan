"""Data types shared by every scanner.

A scanner reads a file and returns a list of Finding objects. Each Finding is
one thing that could help identify a person (or leak details about a lab).
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum
from typing import Optional


class Severity(IntEnum):
    """How worried you should be. IntEnum means LOW < MEDIUM < HIGH works."""

    LOW = 1      # context that helps link files together (dates, commands)
    MEDIUM = 2   # points at a lab, machine, server, or sample
    HIGH = 3     # points at a specific person (username, email, name, DOB)

    @classmethod
    def from_name(cls, name: str) -> "Severity":
        return cls[name.upper()]


@dataclass(frozen=True)
class Finding:
    file: str
    line: Optional[int]   # line number in the file, if it applies
    severity: Severity
    rule: str             # short machine-readable ID, e.g. "home-directory"
    message: str          # human explanation of why this matters
    evidence: str         # the text that triggered the rule

    def to_dict(self) -> dict:
        return {
            "file": self.file,
            "line": self.line,
            "severity": self.severity.name,
            "rule": self.rule,
            "message": self.message,
            "evidence": self.evidence,
        }
