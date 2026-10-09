#!/usr/bin/env python3
"""Add pinned-source metadata to a saved Bambu Studio colour document."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import date
from pathlib import Path
from typing import Any

from validate_catalogue import CatalogueValidationError, load_json
from validate_catalogue_sources import validate_studio_snapshot

REVISION_PATTERN = re.compile(r"^[0-9a-f]{40}$")


def prepare(
    raw: dict[str, Any],
    revision: str,
    retrieved_at: str,
    source_document_sha256: str,
) -> dict[str, Any]:
    if not REVISION_PATTERN.fullmatch(revision):
        raise CatalogueValidationError("revision must be a 40-character lowercase Git commit")
    try:
        date.fromisoformat(retrieved_at)
    except ValueError as error:
        raise CatalogueValidationError("retrieved-at must be an ISO date") from error

    records = raw.get("data")
    if not isinstance(records, list):
        raise CatalogueValidationError("upstream Studio document must contain a data array")

    snapshot = {
        "sourceRevision": revision,
        "sourceDocumentSHA256": source_document_sha256,
        "retrievedAt": retrieved_at,
        "data": records,
    }
    errors = validate_studio_snapshot(snapshot)
    if errors:
        raise CatalogueValidationError("; ".join(errors))
    return snapshot


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--revision", required=True)
    parser.add_argument("--retrieved-at", required=True)
    parser.add_argument("--output", required=True, type=Path)
    arguments = parser.parse_args()

    try:
        raw_bytes = arguments.input.read_bytes()
        raw = load_json(arguments.input)
        snapshot = prepare(
            raw,
            arguments.revision,
            arguments.retrieved_at,
            hashlib.sha256(raw_bytes).hexdigest(),
        )
    except CatalogueValidationError as error:
        print(f"Studio snapshot preparation failed: {error}", file=sys.stderr)
        return 1

    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    arguments.output.write_text(
        json.dumps(snapshot, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"Prepared {len(snapshot['data'])} Studio records from {arguments.revision}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
