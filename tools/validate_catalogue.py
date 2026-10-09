#!/usr/bin/env python3
"""Validate a canonical Filaments catalogue without network access."""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date, datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

SUPPORTED_SCHEMA_VERSION = 1
AVAILABILITY = {"active", "discontinued", "reviewNeeded", "historical", "unknown"}
SOLD_AS = {"spool", "refill", "both"}
SWATCH_TYPES = {"solid", "gradient", "multicolour", "translucent"}
COLOUR_PATTERN = re.compile(r"^#[0-9A-Fa-f]{8}$")
REVISION_PATTERN = re.compile(r"^[0-9a-f]{40}$")
CHECKSUM_PATTERN = re.compile(r"^[0-9a-f]{64}$")
REQUIRED_ENTRY_FIELDS = {
    "key",
    "manufacturer",
    "profileId",
    "colourVariantId",
    "colourCode",
    "materialFamily",
    "materialVariant",
    "name",
    "alternateNames",
    "swatchType",
    "colours",
    "availability",
    "soldAs",
    "firstSeen",
    "sourceEvidence",
}


class CatalogueValidationError(ValueError):
    pass


def is_non_empty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def is_iso_date(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    try:
        date.fromisoformat(value)
    except ValueError:
        return False
    return True


def is_iso_timestamp(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return False
    return True


def is_australian_store_url(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    parsed = urlparse(value)
    return parsed.scheme == "https" and parsed.hostname == "au.store.bambulab.com"


def load_json(path: Path) -> dict[str, Any]:
    try:
        with path.open(encoding="utf-8") as catalogue_file:
            value = json.load(catalogue_file)
    except (OSError, json.JSONDecodeError) as error:
        raise CatalogueValidationError(f"couldn't read {path}: {error}") from error
    if not isinstance(value, dict):
        raise CatalogueValidationError("catalogue root must be an object")
    return value


def validate(document: dict[str, Any], previous: dict[str, Any] | None = None) -> list[str]:
    errors: list[str] = []
    if document.get("schemaVersion") != SUPPORTED_SCHEMA_VERSION:
        errors.append(f"schemaVersion must be {SUPPORTED_SCHEMA_VERSION}")
    if document.get("region") != "AU":
        errors.append("region must be AU")
    for field_name in ("catalogueVersion", "generatorVersion"):
        if not is_non_empty_string(document.get(field_name)):
            errors.append(f"{field_name} must be a non-empty string")
    if not is_iso_timestamp(document.get("generatedAt")):
        errors.append("generatedAt must be an ISO timestamp")
    if not isinstance(document.get("sourceStudioRevision"), str) or not REVISION_PATTERN.fullmatch(
        document["sourceStudioRevision"]
    ):
        errors.append("sourceStudioRevision must be a 40-character lowercase Git commit")

    retrieval_dates = document.get("sourceRetrievalDates")
    if not isinstance(retrieval_dates, dict):
        errors.append("sourceRetrievalDates must be an object")
    else:
        for source_name in ("bambuStudio", "australianStore"):
            if not is_iso_date(retrieval_dates.get(source_name)):
                errors.append(f"sourceRetrievalDates.{source_name} must be an ISO date")

    content_checksum = document.get("contentChecksum")
    if content_checksum is not None and (
        not isinstance(content_checksum, str) or not CHECKSUM_PATTERN.fullmatch(content_checksum)
    ):
        errors.append("contentChecksum must be null or a lowercase SHA-256 digest")

    entries = document.get("entries")
    if not isinstance(entries, list):
        return errors + ["entries must be an array"]
    if document.get("entryCount") != len(entries):
        errors.append(f"entryCount is {document.get('entryCount')!r}, expected {len(entries)}")

    entries_by_key: dict[str, dict[str, Any]] = {}
    for index, entry in enumerate(entries):
        label = f"entries[{index}]"
        if not isinstance(entry, dict):
            errors.append(f"{label} must be an object")
            continue

        missing = sorted(REQUIRED_ENTRY_FIELDS - entry.keys())
        if missing:
            errors.append(f"{label} is missing: {', '.join(missing)}")
            continue

        key = entry["key"]
        if not is_non_empty_string(key):
            errors.append(f"{label}: key must be a non-empty string")
        else:
            label = key
            if key in entries_by_key:
                errors.append(f"duplicate key: {key}")
            else:
                entries_by_key[key] = entry

        expected_key = f"{entry['profileId']}:{entry['colourVariantId']}"
        if key != expected_key:
            errors.append(f"{label}: key must be {expected_key}")

        for field in (
            "manufacturer",
            "profileId",
            "colourVariantId",
            "colourCode",
            "materialFamily",
            "materialVariant",
            "name",
            "firstSeen",
        ):
            if not is_non_empty_string(entry[field]):
                errors.append(f"{label}: {field} must be a non-empty string")
        if entry["manufacturer"] != "Bambu Lab":
            errors.append(f"{label}: manufacturer must be Bambu Lab")

        if not isinstance(entry["availability"], str) or entry["availability"] not in AVAILABILITY:
            errors.append(f"{label}: unknown availability {entry['availability']!r}")
        if not isinstance(entry["soldAs"], str) or entry["soldAs"] not in SOLD_AS:
            errors.append(f"{label}: unknown soldAs {entry['soldAs']!r}")
        if not isinstance(entry["swatchType"], str) or entry["swatchType"] not in SWATCH_TYPES:
            errors.append(f"{label}: unknown swatchType {entry['swatchType']!r}")

        alternate_names = entry["alternateNames"]
        if not isinstance(alternate_names, list) or any(
            not is_non_empty_string(name) for name in alternate_names
        ):
            errors.append(f"{label}: alternateNames must be an array of non-empty strings")

        last_seen_active = entry.get("lastSeenActive")
        if last_seen_active is not None and not is_iso_date(last_seen_active):
            errors.append(f"{label}: lastSeenActive must be null or an ISO date")

        colours = entry["colours"]
        if not isinstance(colours, list) or not colours:
            errors.append(f"{label}: colours must contain at least one value")
        elif any(not isinstance(colour, str) or not COLOUR_PATTERN.fullmatch(colour) for colour in colours):
            errors.append(f"{label}: colours must use #RRGGBBAA")
        if (
            isinstance(entry["swatchType"], str)
            and entry["swatchType"] in {"gradient", "multicolour"}
            and isinstance(colours, list)
            and len(colours) < 2
        ):
            errors.append(f"{label}: {entry['swatchType']} needs at least two colours")

        evidence = entry["sourceEvidence"]
        if not isinstance(evidence, dict) or not is_non_empty_string(evidence.get("studioPath")):
            errors.append(f"{label}: sourceEvidence.studioPath is required")
        if isinstance(evidence, dict) and evidence.get("note") is not None and not isinstance(
            evidence.get("note"), str
        ):
            errors.append(f"{label}: sourceEvidence.note must be null or a string")
        if entry["availability"] == "active" and (
            not isinstance(evidence, dict) or not evidence.get("australianStoreURL")
        ):
            errors.append(f"{label}: active entries need Australian store evidence")
        for field_name, value in (
            ("productURL", entry.get("productURL")),
            (
                "sourceEvidence.australianStoreURL",
                evidence.get("australianStoreURL") if isinstance(evidence, dict) else None,
            ),
        ):
            if value is not None and not is_australian_store_url(value):
                errors.append(f"{label}: {field_name} must be an HTTPS Bambu Lab AU store URL")

    if previous is not None:
        previous_entries = previous.get("entries", [])
        previous_by_key = {
            entry["key"]: entry
            for entry in previous_entries
            if isinstance(entry, dict) and is_non_empty_string(entry.get("key"))
        }
        removed = sorted(previous_by_key.keys() - entries_by_key.keys())
        if removed:
            errors.append(f"entries removed from the previous catalogue: {', '.join(removed)}")
        for key in previous_by_key.keys() & entries_by_key.keys():
            old = previous_by_key[key]
            new = entries_by_key[key]
            for field in ("profileId", "colourVariantId"):
                if old.get(field) != new.get(field):
                    errors.append(f"{key}: stable identity field {field} was reassigned")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("catalogue", type=Path)
    parser.add_argument("--previous", type=Path)
    arguments = parser.parse_args()

    try:
        document = load_json(arguments.catalogue)
        previous = load_json(arguments.previous) if arguments.previous else None
    except CatalogueValidationError as error:
        print(f"Catalogue validation failed: {error}", file=sys.stderr)
        return 1

    errors = validate(document, previous)
    if errors:
        print("Catalogue validation failed:", file=sys.stderr)
        for error in errors:
            print(f"  - {error}", file=sys.stderr)
        return 1

    print(f"Validated {len(document['entries'])} entries in catalogue {document['catalogueVersion']}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
