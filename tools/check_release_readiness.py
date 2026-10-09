#!/usr/bin/env python3
"""Check that offline catalogue artefacts are internally ready for a release build."""

from __future__ import annotations

import argparse
import hashlib
import re
import sys
from datetime import date
from pathlib import Path
from typing import Any

from generate_catalogue import validate_overrides
from prepare_store_review import validate_review
from validate_catalogue import CatalogueValidationError, load_json, validate
from validate_catalogue_sources import validate_store_snapshot, validate_studio_snapshot

RELEASE_AVAILABILITY = {"active", "discontinued", "historical"}
MANIFEST_INPUTS = ("studio", "store", "overrides", "previous")
MANIFEST_OUTPUTS = ("catalogue", "report")
RELEASE_VERSION_PATTERN = re.compile(r"^(\d{4})\.(\d{2})\.(\d{2})\.(\d+)$")
VERSION_PREFIX_PATTERN = re.compile(r"^(\d{4})\.(\d{2})\.(\d{2})\.(\d+)")


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def version_key(value: Any, release: bool = False) -> tuple[int, int, int, int] | None:
    if not isinstance(value, str):
        return None
    pattern = RELEASE_VERSION_PATTERN if release else VERSION_PREFIX_PATTERN
    match = pattern.fullmatch(value) if release else pattern.match(value)
    if match is None:
        return None
    year, month, day, sequence = (int(part) for part in match.groups())
    try:
        date(year, month, day)
    except ValueError:
        return None
    return year, month, day, sequence


def release_readiness_errors(
    catalogue: dict[str, Any],
    previous: dict[str, Any],
    studio: dict[str, Any],
    store: dict[str, Any],
    overrides: dict[str, Any],
    manifest: dict[str, Any],
    store_review: dict[str, Any],
    report_text: str,
    artefact_paths: dict[str, Path],
) -> list[str]:
    errors = validate(catalogue, previous)
    errors += validate_studio_snapshot(studio)
    errors += validate_store_snapshot(store, require_approved=True)
    errors += validate_review(
        store_review,
        studio,
        store,
        artefact_paths["studio"],
        artefact_paths["store"],
        artefact_paths["audit"],
        require_complete=True,
    )

    review_metadata = store.get("review")
    signoff = review_metadata.get("signoff") if isinstance(review_metadata, dict) else None
    if isinstance(signoff, dict):
        if signoff.get("reviewSHA256") != file_sha256(artefact_paths["review"]):
            errors.append("approved store review hash doesn't match the sign-off file")
        if signoff.get("collectionAuditSHA256") != file_sha256(artefact_paths["audit"]):
            errors.append("approved store audit hash doesn't match the collection audit")

    try:
        validate_overrides(overrides)
    except CatalogueValidationError as error:
        errors.append(str(error))

    version = catalogue.get("catalogueVersion")
    if not isinstance(version, str) or not version.strip():
        errors.append("catalogueVersion must be a non-empty string")
    else:
        if any(marker in version.casefold() for marker in ("draft", "prototype")):
            errors.append("release catalogueVersion must not contain draft or prototype")
        current_version_key = version_key(version, release=True)
        if current_version_key is None:
            errors.append("release catalogueVersion must use YYYY.MM.DD.N")
        previous_version = previous.get("catalogueVersion")
        previous_version_key = version_key(previous_version)
        if previous_version_key is None:
            errors.append("previous catalogueVersion must start with YYYY.MM.DD.N")
        elif current_version_key is not None and current_version_key <= previous_version_key:
            errors.append("release catalogueVersion must be newer than the previous catalogue")

    entries = catalogue.get("entries", [])
    if isinstance(entries, list):
        unresolved = sorted(
            entry.get("key", f"entries[{index}]")
            for index, entry in enumerate(entries)
            if isinstance(entry, dict) and entry.get("availability") not in RELEASE_AVAILABILITY
        )
        if unresolved:
            errors.append(
                "release catalogue has unresolved availability: " + ", ".join(unresolved)
            )

    store_keys = {
        f"{variant.get('profileId')}:{variant.get('colourVariantId')}"
        for product in store.get("products", [])
        if isinstance(product, dict)
        for variant in product.get("variants", [])
        if isinstance(variant, dict)
    }
    catalogue_keys = {
        entry.get("key") for entry in entries if isinstance(entry, dict)
    }
    missing_store_keys = sorted(store_keys - catalogue_keys)
    if missing_store_keys:
        errors.append(
            "approved store mappings missing from catalogue: " + ", ".join(missing_store_keys)
        )

    active_keys = {
        entry.get("key")
        for entry in entries
        if isinstance(entry, dict) and entry.get("availability") == "active"
    }
    active_without_store_evidence = sorted(active_keys - store_keys)
    if active_without_store_evidence:
        errors.append(
            "active catalogue entries missing from the approved store snapshot: "
            + ", ".join(active_without_store_evidence)
        )

    expected_metadata = {
        "catalogueVersion": version,
        "generatedAt": catalogue.get("generatedAt"),
        "generatorVersion": catalogue.get("generatorVersion"),
        "sourceStudioRevision": studio.get("sourceRevision"),
    }
    for field_name, expected in expected_metadata.items():
        if manifest.get(field_name) != expected:
            errors.append(f"manifest {field_name} doesn't match the catalogue sources")

    if catalogue.get("sourceStudioRevision") != studio.get("sourceRevision"):
        errors.append("catalogue sourceStudioRevision doesn't match the Studio snapshot")
    retrieval_dates = catalogue.get("sourceRetrievalDates")
    if not isinstance(retrieval_dates, dict):
        errors.append("catalogue sourceRetrievalDates must be an object")
    else:
        if retrieval_dates.get("bambuStudio") != studio.get("retrievedAt"):
            errors.append("catalogue Bambu Studio retrieval date doesn't match its snapshot")
        if retrieval_dates.get("australianStore") != store.get("retrievedAt"):
            errors.append("catalogue Australian store retrieval date doesn't match its snapshot")

    if manifest.get("storeReview") != store.get("review"):
        errors.append("manifest storeReview doesn't match the store snapshot")

    manifest_inputs = manifest.get("inputs")
    if not isinstance(manifest_inputs, dict):
        errors.append("manifest inputs must be an object")
    else:
        for input_name in MANIFEST_INPUTS:
            record = manifest_inputs.get(input_name)
            path = artefact_paths[input_name]
            if not isinstance(record, dict):
                errors.append(f"manifest input {input_name} must be an object")
                continue
            if record.get("sha256") != file_sha256(path):
                errors.append(f"manifest hash doesn't match {input_name} input")

    manifest_outputs = manifest.get("outputs")
    if not isinstance(manifest_outputs, dict):
        errors.append("manifest outputs must be an object")
    else:
        for output_name in MANIFEST_OUTPUTS:
            record = manifest_outputs.get(output_name)
            path = artefact_paths[output_name]
            if not isinstance(record, dict):
                errors.append(f"manifest output {output_name} must be an object")
                continue
            if record.get("sha256") != file_sha256(path):
                errors.append(f"manifest hash doesn't match {output_name} output")

    expected_report_markers = (
        f"# Catalogue review: {version}",
        "Store snapshot review: approved",
        "## Unmatched store variants\n\nNone.",
        "## Warnings\n\nNone.",
    )
    for marker in expected_report_markers:
        if marker not in report_text:
            errors.append(f"review report is missing release marker: {marker.splitlines()[0]}")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalogue", required=True, type=Path)
    parser.add_argument("--previous", required=True, type=Path)
    parser.add_argument("--studio", required=True, type=Path)
    parser.add_argument("--store", required=True, type=Path)
    parser.add_argument("--overrides", required=True, type=Path)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--report", required=True, type=Path)
    parser.add_argument("--review-signoff", required=True, type=Path)
    parser.add_argument("--collection-audit", required=True, type=Path)
    arguments = parser.parse_args()

    try:
        catalogue = load_json(arguments.catalogue)
        previous = load_json(arguments.previous)
        studio = load_json(arguments.studio)
        store = load_json(arguments.store)
        overrides = load_json(arguments.overrides)
        manifest = load_json(arguments.manifest)
        store_review = load_json(arguments.review_signoff)
        report_text = arguments.report.read_text(encoding="utf-8")
        arguments.collection_audit.read_bytes()
    except (CatalogueValidationError, OSError) as error:
        print(f"Release readiness check failed: {error}", file=sys.stderr)
        return 1

    errors = release_readiness_errors(
        catalogue,
        previous,
        studio,
        store,
        overrides,
        manifest,
        store_review,
        report_text,
        {
            "studio": arguments.studio,
            "store": arguments.store,
            "overrides": arguments.overrides,
            "previous": arguments.previous,
            "catalogue": arguments.catalogue,
            "report": arguments.report,
            "review": arguments.review_signoff,
            "audit": arguments.collection_audit,
        },
    )
    if errors:
        print("Release readiness check failed:", file=sys.stderr)
        for error in errors:
            print(f"  - {error}", file=sys.stderr)
        return 1

    print(
        f"Release catalogue {catalogue['catalogueVersion']} is internally consistent "
        f"with {catalogue['entryCount']} entries."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
