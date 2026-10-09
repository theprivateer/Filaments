#!/usr/bin/env python3
"""Reject runtime networking code from the local-only Filaments app target."""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ForbiddenPattern:
    label: str
    expression: re.Pattern[str]


FORBIDDEN_PATTERNS = (
    ForbiddenPattern("Network framework import", re.compile(r"^\s*import\s+Network\b")),
    ForbiddenPattern("WebKit framework import", re.compile(r"^\s*import\s+WebKit\b")),
    ForbiddenPattern("URLSession", re.compile(r"\bURLSession\b")),
    ForbiddenPattern("URLRequest", re.compile(r"\bURLRequest\b")),
    ForbiddenPattern("Network.framework type", re.compile(r"\bNW[A-Z][A-Za-z0-9_]*\b")),
    ForbiddenPattern("web view", re.compile(r"\bWKWebView\b")),
    ForbiddenPattern("in-app browser", re.compile(r"\bSFSafariViewController\b")),
    ForbiddenPattern("web socket", re.compile(r"\b(?:URLSessionWebSocketTask|WebSocket)\b")),
)


def validate_source_tree(root: Path) -> list[str]:
    errors: list[str] = []
    if not root.is_dir():
        return [f"app source directory doesn't exist: {root}"]

    source_files = sorted(root.rglob("*.swift"))
    if not source_files:
        return [f"app source directory contains no Swift files: {root}"]

    for path in source_files:
        relative_path = path.relative_to(root)
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except OSError as error:
            errors.append(f"couldn't read {relative_path}: {error}")
            continue
        for line_number, line in enumerate(lines, start=1):
            for forbidden in FORBIDDEN_PATTERNS:
                if forbidden.expression.search(line):
                    errors.append(
                        f"{relative_path}:{line_number}: {forbidden.label} isn't allowed "
                        "in the local-only app target"
                    )
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source_directory", type=Path)
    arguments = parser.parse_args()

    errors = validate_source_tree(arguments.source_directory)
    if errors:
        print("Runtime policy validation failed:", file=sys.stderr)
        for error in errors:
            print(f"  - {error}", file=sys.stderr)
        return 1

    print(
        f"Validated local-only runtime policy in {arguments.source_directory}. "
        "External system-browser links remain allowed."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
