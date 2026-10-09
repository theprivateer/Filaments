#!/usr/bin/env python3
"""Validate saved Bambu Studio and reviewed Australian store snapshots."""

from __future__ import annotations

import argparse
import re
import sys
from datetime import date
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from validate_catalogue import CatalogueValidationError, load_json

COLOUR_PATTERN = re.compile(r"^#[0-9A-Fa-f]{8}$")
REVISION_PATTERN = re.compile(r"^[0-9a-f]{40}$")
SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")
SOLD_AS = {"spool", "refill", "both"}
REVIEW_STATUSES = {"draft", "approved"}


def stable_key(profile_id: str, colour_variant_id: str) -> str:
    return f"{profile_id}:{colour_variant_id}"


def valid_date(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    try:
        date.fromisoformat(value)
    except ValueError:
        return False
    return True


def non_empty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def validate_studio_snapshot(snapshot: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if not isinstance(snapshot.get("sourceRevision"), str) or not REVISION_PATTERN.fullmatch(
        snapshot["sourceRevision"]
    ):
        errors.append("Studio sourceRevision must be a 40-character lowercase Git commit")
    if not isinstance(snapshot.get("sourceDocumentSHA256"), str) or not SHA256_PATTERN.fullmatch(
        snapshot["sourceDocumentSHA256"]
    ):
        errors.append("Studio sourceDocumentSHA256 must be a lowercase SHA-256 digest")
    if not valid_date(snapshot.get("retrievedAt")):
        errors.append("Studio retrievedAt must be an ISO date")

    records = snapshot.get("data")
    if not isinstance(records, list):
        return errors + ["Studio data must be an array"]

    keys: set[str] = set()
    for index, record in enumerate(records):
        label = f"Studio data[{index}]"
        if not isinstance(record, dict):
            errors.append(f"{label} must be an object")
            continue

        for field_name in (
            "fila_id",
            "fila_color_code",
            "fila_color_type",
            "fila_type",
            "color_code",
        ):
            if not non_empty_string(record.get(field_name)):
                errors.append(f"{label}.{field_name} must be a non-empty string")

        names = record.get("fila_color_name")
        if not isinstance(names, dict) or not non_empty_string(names.get("en")):
            errors.append(f"{label}.fila_color_name.en must be a non-empty string")

        colours = record.get("fila_color")
        if not isinstance(colours, list) or not colours:
            errors.append(f"{label}.fila_color must contain at least one value")
        elif any(not isinstance(value, str) or not COLOUR_PATTERN.fullmatch(value) for value in colours):
            errors.append(f"{label}.fila_color values must use #RRGGBBAA")

        profile_id = record.get("fila_id")
        colour_variant_id = record.get("fila_color_code")
        if non_empty_string(profile_id) and non_empty_string(colour_variant_id):
            key = stable_key(profile_id, colour_variant_id)
            if key in keys:
                errors.append(f"duplicate Studio identity: {key}")
            keys.add(key)
    return errors


def validate_store_snapshot(
    snapshot: dict[str, Any],
    require_approved: bool = False,
) -> list[str]:
    errors: list[str] = []
    if snapshot.get("region") != "AU":
        errors.append("store region must be AU")
    if not valid_date(snapshot.get("retrievedAt")):
        errors.append("store retrievedAt must be an ISO date")

    review = snapshot.get("review")
    if not isinstance(review, dict):
        errors.append("store review must be an object")
    else:
        status = review.get("status")
        if status not in REVIEW_STATUSES:
            errors.append("store review.status must be draft or approved")
        if status == "approved":
            if not non_empty_string(review.get("reviewedBy")):
                errors.append("approved store snapshots need review.reviewedBy")
            if not valid_date(review.get("reviewedAt")):
                errors.append("approved store snapshots need an ISO review.reviewedAt date")
            signoff = review.get("signoff")
            if not isinstance(signoff, dict):
                errors.append("approved store snapshots need review.signoff")
            else:
                for field_name in ("path", "collectionAuditPath"):
                    if not non_empty_string(signoff.get(field_name)):
                        errors.append(
                            f"approved store snapshots need review.signoff.{field_name}"
                        )
                for field_name in ("reviewSHA256", "collectionAuditSHA256"):
                    value = signoff.get(field_name)
                    if not isinstance(value, str) or not SHA256_PATTERN.fullmatch(value):
                        errors.append(
                            f"approved store snapshots need review.signoff.{field_name}"
                        )
        if require_approved and status != "approved":
            errors.append("store snapshot must be approved for this operation")

    products = snapshot.get("products")
    if not isinstance(products, list):
        return errors + ["store products must be an array"]

    keys: set[str] = set()
    for product_index, product in enumerate(products):
        label = f"store products[{product_index}]"
        if not isinstance(product, dict):
            errors.append(f"{label} must be an object")
            continue

        for field_name in ("materialFamily", "materialVariant"):
            if not non_empty_string(product.get(field_name)):
                errors.append(f"{label}.{field_name} must be a non-empty string")

        product_url = product.get("productURL")
        if product_url is not None and not valid_au_store_url(product_url):
            errors.append(f"{label}.productURL must be an HTTPS Bambu Lab AU store URL")
        if product.get("soldAs") not in SOLD_AS:
            errors.append(f"{label}.soldAs must be spool, refill or both")
        if not valid_date(product.get("confirmedAt")):
            errors.append(f"{label}.confirmedAt must be an ISO date")

        variants = product.get("variants")
        if not isinstance(variants, list) or not variants:
            errors.append(f"{label}.variants must contain at least one variant")
            continue
        for variant_index, variant in enumerate(variants):
            variant_label = f"{label}.variants[{variant_index}]"
            if not isinstance(variant, dict):
                errors.append(f"{variant_label} must be an object")
                continue
            profile_id = variant.get("profileId")
            colour_variant_id = variant.get("colourVariantId")
            if not non_empty_string(profile_id):
                errors.append(f"{variant_label}.profileId must be a non-empty string")
            if not non_empty_string(colour_variant_id):
                errors.append(f"{variant_label}.colourVariantId must be a non-empty string")
            if "soldAs" in variant and variant.get("soldAs") not in SOLD_AS:
                errors.append(f"{variant_label}.soldAs must be spool, refill or both")
            if non_empty_string(profile_id) and non_empty_string(colour_variant_id):
                key = stable_key(profile_id, colour_variant_id)
                if key in keys:
                    errors.append(f"store identity is mapped more than once: {key}")
                keys.add(key)
    return errors


def valid_au_store_url(value: Any) -> bool:
    if not non_empty_string(value):
        return False
    parsed = urlparse(value)
    return parsed.scheme == "https" and parsed.hostname == "au.store.bambulab.com"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--studio", required=True, type=Path)
    parser.add_argument("--store", required=True, type=Path)
    parser.add_argument("--require-approved-store", action="store_true")
    arguments = parser.parse_args()

    try:
        studio = load_json(arguments.studio)
        store = load_json(arguments.store)
    except CatalogueValidationError as error:
        print(f"Source validation failed: {error}", file=sys.stderr)
        return 1

    errors = validate_studio_snapshot(studio)
    errors += validate_store_snapshot(store, arguments.require_approved_store)
    if errors:
        print("Source validation failed:", file=sys.stderr)
        for error in errors:
            print(f"  - {error}", file=sys.stderr)
        return 1

    review_status = store["review"]["status"]
    print(
        f"Validated {len(studio['data'])} Studio records and "
        f"{len(store['products'])} AU products ({review_status})."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
