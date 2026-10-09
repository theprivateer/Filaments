#!/usr/bin/env python3
"""Generate a reviewable canonical catalogue from saved offline snapshots."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from validate_catalogue import CatalogueValidationError, load_json, validate
from validate_catalogue_sources import validate_store_snapshot, validate_studio_snapshot

MULTICOLOUR_SOURCE_TYPES = {"多拼色", "多色", "多色彩"}


@dataclass
class GenerationReport:
    additions: list[str] = field(default_factory=list)
    changes: list[str] = field(default_factory=list)
    missing: list[str] = field(default_factory=list)
    reactivated: list[str] = field(default_factory=list)
    unmatched: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def stable_key(profile_id: str, colour_variant_id: str) -> str:
    return f"{profile_id}:{colour_variant_id}"


def infer_swatch_type(source: dict[str, Any]) -> str:
    colours = source.get("fila_color", [])
    source_type = source.get("fila_color_type", "")
    if len(colours) > 1:
        return "multicolour" if source_type in MULTICOLOUR_SOURCE_TYPES else "gradient"
    if colours and colours[0][-2:].upper() != "FF":
        return "translucent"
    return "solid"


def index_studio_records(snapshot: dict[str, Any]) -> dict[str, dict[str, Any]]:
    records = snapshot.get("data")
    if not isinstance(records, list):
        raise CatalogueValidationError("Bambu Studio snapshot must contain a data array")

    result: dict[str, dict[str, Any]] = {}
    for record in records:
        if not isinstance(record, dict):
            raise CatalogueValidationError("Bambu Studio data entries must be objects")
        key = stable_key(str(record.get("fila_id", "")), str(record.get("fila_color_code", "")))
        if key in result:
            raise CatalogueValidationError(f"duplicate Bambu Studio identity: {key}")
        result[key] = record
    return result


def index_store_variants(snapshot: dict[str, Any]) -> dict[str, dict[str, Any]]:
    if snapshot.get("region") != "AU":
        raise CatalogueValidationError("store snapshot region must be AU")
    products = snapshot.get("products")
    if not isinstance(products, list):
        raise CatalogueValidationError("store snapshot must contain a products array")

    result: dict[str, dict[str, Any]] = {}
    for product in products:
        for variant in product.get("variants", []):
            key = stable_key(str(variant.get("profileId", "")), str(variant.get("colourVariantId", "")))
            if key in result:
                raise CatalogueValidationError(f"store identity is mapped more than once: {key}")
            result[key] = {**product, **variant, "variants": None}
    return result


def validate_overrides(overrides: dict[str, Any]) -> dict[str, dict[str, Any]]:
    entries = overrides.get("entries", {})
    if not isinstance(entries, dict):
        raise CatalogueValidationError("overrides.entries must be an object")
    for key, override in entries.items():
        if not isinstance(override, dict) or not override.get("reason") or not override.get("source"):
            raise CatalogueValidationError(f"override {key} needs a reason and source")
    return entries


def build_entry(
    key: str,
    studio: dict[str, Any],
    store: dict[str, Any],
    catalogue_version: str,
) -> dict[str, Any]:
    colour_names = studio.get("fila_color_name", {})
    name = colour_names.get("en")
    product_url = store.get("productURL")
    return {
        "key": key,
        "manufacturer": "Bambu Lab",
        "profileId": studio["fila_id"],
        "colourVariantId": studio["fila_color_code"],
        "colourCode": studio.get("color_code", ""),
        "materialFamily": store["materialFamily"],
        "materialVariant": store.get("materialVariant") or studio["fila_type"],
        "name": store.get("displayName") or name,
        "alternateNames": sorted(set(store.get("alternateNames", []))),
        "swatchType": store.get("swatchType") or infer_swatch_type(studio),
        "colours": studio["fila_color"],
        "availability": store.get("availability", "active"),
        "soldAs": store["soldAs"],
        "productURL": product_url,
        "firstSeen": catalogue_version,
        "lastSeenActive": store.get("confirmedAt") if store.get("availability", "active") == "active" else None,
        "sourceEvidence": {
            "studioPath": f"resources/profiles/BBL/filament/filaments_color_codes.json#{key}",
            "australianStoreURL": product_url,
            "note": store.get("evidenceNote"),
        },
    }


def apply_override(entry: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    result = dict(entry)
    allowed = {
        "name",
        "materialFamily",
        "materialVariant",
        "swatchType",
        "colours",
        "availability",
        "soldAs",
        "productURL",
        "lastSeenActive",
    }
    for field_name in allowed & override.keys():
        result[field_name] = override[field_name]
    if "alternateNamesAdd" in override:
        result["alternateNames"] = sorted(
            set(result.get("alternateNames", [])) | set(override["alternateNamesAdd"])
        )
    result["sourceEvidence"] = dict(result["sourceEvidence"])
    result["sourceEvidence"]["note"] = (
        f"Override: {override['reason']} Source: {override['source']}"
    )
    return result


def generate(
    studio_snapshot: dict[str, Any],
    store_snapshot: dict[str, Any],
    overrides_document: dict[str, Any],
    previous: dict[str, Any] | None,
    catalogue_version: str,
    generated_at: str,
    studio_revision: str,
    generator_version: str = "0.3.1",
) -> tuple[dict[str, Any], GenerationReport]:
    source_errors = validate_studio_snapshot(studio_snapshot)
    source_errors += validate_store_snapshot(store_snapshot)
    if source_errors:
        raise CatalogueValidationError("; ".join(source_errors))
    if studio_snapshot["sourceRevision"] != studio_revision:
        raise CatalogueValidationError(
            "Studio snapshot revision doesn't match --studio-revision: "
            f"{studio_snapshot['sourceRevision']} != {studio_revision}"
        )

    studio_by_key = index_studio_records(studio_snapshot)
    store_by_key = index_store_variants(store_snapshot)
    overrides = validate_overrides(overrides_document)
    previous_by_key = {
        entry["key"]: entry for entry in (previous or {}).get("entries", [])
    }
    report = GenerationReport()
    entries_by_key: dict[str, dict[str, Any]] = {}

    for key, store in store_by_key.items():
        studio = studio_by_key.get(key)
        if studio is None:
            report.unmatched.append(key)
            continue
        entry = build_entry(key, studio, store, catalogue_version)
        if entry["availability"] == "reviewNeeded":
            detail = store.get("evidenceNote") or "source evidence needs human review"
            report.warnings.append(f"{key} is reviewNeeded: {detail}")
        if not store.get("productURL"):
            if entry["availability"] == "active":
                entry["availability"] = "reviewNeeded"
                entry["lastSeenActive"] = None
            report.warnings.append(f"{key} has no Australian product URL and needs review")
        override = overrides.get(key)
        if override:
            if override.get("exclude"):
                report.warnings.append(f"{key} excluded by reviewed override")
                continue
            entry = apply_override(entry, override)
        if key in previous_by_key:
            entry["firstSeen"] = previous_by_key[key]["firstSeen"]
        entries_by_key[key] = entry

    for key, old_entry in previous_by_key.items():
        if key in entries_by_key:
            if old_entry.get("availability") == "discontinued" and entries_by_key[key]["availability"] == "active":
                report.reactivated.append(key)
            continue
        retained = dict(old_entry)
        if retained.get("availability") == "active":
            retained["availability"] = "reviewNeeded"
        entries_by_key[key] = retained
        report.missing.append(key)

    for key, override in overrides.items():
        if key not in entries_by_key and key not in store_by_key:
            report.warnings.append(f"override {key} doesn't match a current or previous entry")

    ordered_entries = sorted(
        entries_by_key.values(),
        key=lambda entry: (
            entry["materialFamily"].casefold(),
            entry["materialVariant"].casefold(),
            entry["name"].casefold(),
            entry["key"],
        ),
    )
    document = {
        "schemaVersion": 1,
        "catalogueVersion": catalogue_version,
        "generatedAt": generated_at,
        "region": "AU",
        "generatorVersion": generator_version,
        "sourceStudioRevision": studio_revision,
        "sourceRetrievalDates": {
            "bambuStudio": studio_snapshot["retrievedAt"],
            "australianStore": store_snapshot["retrievedAt"],
        },
        "entryCount": len(ordered_entries),
        "contentChecksum": None,
        "entries": ordered_entries,
    }

    validation_errors = validate(document, previous)
    if validation_errors:
        raise CatalogueValidationError("; ".join(validation_errors))

    previous_keys = set(previous_by_key)
    current_keys = set(entries_by_key)
    report.additions = sorted(current_keys - previous_keys)
    for key in sorted(current_keys & previous_keys):
        old = previous_by_key[key]
        new = entries_by_key[key]
        changed_fields = [
            field_name
            for field_name in (
                "name",
                "materialFamily",
                "materialVariant",
                "swatchType",
                "colours",
                "availability",
                "soldAs",
                "productURL",
            )
            if old.get(field_name) != new.get(field_name)
        ]
        if changed_fields:
            report.changes.append(f"{key}: {', '.join(changed_fields)}")
    return document, report


def render_report(
    document: dict[str, Any],
    report: GenerationReport,
    store_review: dict[str, Any] | None = None,
) -> str:
    family_counts = Counter(entry["materialFamily"] for entry in document["entries"])

    def section(title: str, values: list[str]) -> list[str]:
        return [f"## {title}", "", *([f"- {value}" for value in values] or ["None."]), ""]

    lines = [
        f"# Catalogue review: {document['catalogueVersion']}",
        "",
        f"Generated: {document['generatedAt']}",
        "",
        f"Entries: {document['entryCount']}",
        "",
    ]
    if store_review is not None:
        lines += [
            f"Store snapshot review: {store_review['status']}",
            "",
            f"Reviewer: {store_review.get('reviewedBy') or 'Pending'}",
            "",
        ]
    lines += section("Additions", report.additions)
    lines += section("Changed entries", report.changes)
    lines += section("Missing from current store snapshot", report.missing)
    lines += section("Reactivated", report.reactivated)
    lines += section("Unmatched store variants", report.unmatched)
    lines += section("Warnings", report.warnings)
    lines += ["## Entries by material family", ""]
    lines += [f"- {family}: {count}" for family, count in sorted(family_counts.items())]
    return "\n".join(lines) + "\n"


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, value: dict[str, Any]) -> None:
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--studio", required=True, type=Path)
    parser.add_argument("--store", required=True, type=Path)
    parser.add_argument("--overrides", required=True, type=Path)
    parser.add_argument("--previous", type=Path)
    parser.add_argument("--catalogue-version", required=True)
    parser.add_argument("--studio-revision", required=True)
    parser.add_argument("--generated-at", default=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"))
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--report", required=True, type=Path)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--require-approved-store", action="store_true")
    arguments = parser.parse_args()

    try:
        studio = load_json(arguments.studio)
        store = load_json(arguments.store)
        overrides = load_json(arguments.overrides)
        previous = load_json(arguments.previous) if arguments.previous else None
        approval_errors = validate_store_snapshot(store, arguments.require_approved_store)
        if approval_errors:
            raise CatalogueValidationError("; ".join(approval_errors))
        document, report = generate(
            studio,
            store,
            overrides,
            previous,
            arguments.catalogue_version,
            arguments.generated_at,
            arguments.studio_revision,
        )
    except CatalogueValidationError as error:
        print(f"Catalogue generation failed: {error}", file=sys.stderr)
        return 1

    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    arguments.report.parent.mkdir(parents=True, exist_ok=True)
    arguments.manifest.parent.mkdir(parents=True, exist_ok=True)
    write_json(arguments.output, document)
    arguments.report.write_text(
        render_report(document, report, store["review"]),
        encoding="utf-8",
    )
    manifest = {
        "catalogueVersion": arguments.catalogue_version,
        "generatedAt": arguments.generated_at,
        "generatorVersion": document["generatorVersion"],
        "inputs": {
            "studio": {"path": str(arguments.studio), "sha256": file_sha256(arguments.studio)},
            "store": {"path": str(arguments.store), "sha256": file_sha256(arguments.store)},
            "overrides": {"path": str(arguments.overrides), "sha256": file_sha256(arguments.overrides)},
            "previous": (
                {"path": str(arguments.previous), "sha256": file_sha256(arguments.previous)}
                if arguments.previous
                else None
            ),
        },
        "outputs": {
            "catalogue": {
                "path": str(arguments.output),
                "sha256": file_sha256(arguments.output),
            },
            "report": {
                "path": str(arguments.report),
                "sha256": file_sha256(arguments.report),
            },
        },
        "sourceStudioRevision": arguments.studio_revision,
        "storeReview": store["review"],
    }
    write_json(arguments.manifest, manifest)
    print(f"Generated {document['entryCount']} entries; {len(report.unmatched)} unmatched variants need review.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
