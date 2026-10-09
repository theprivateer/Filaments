#!/usr/bin/env python3
"""Prepare or validate a per-entry human review for an AU store snapshot."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import sys
from datetime import date
from pathlib import Path
from typing import Any

from validate_catalogue import CatalogueValidationError, load_json
from validate_catalogue_sources import validate_store_snapshot, validate_studio_snapshot

DECISIONS = {"pending", "approved", "rejected"}
IMMUTABLE_PRODUCT_FIELDS = (
    "reviewKey",
    "materialFamily",
    "materialVariant",
    "productURL",
    "soldAs",
    "confirmedAt",
    "evidenceNote",
)
IMMUTABLE_VARIANT_FIELDS = (
    "key",
    "name",
    "colours",
    "availability",
    "soldAs",
    "evidenceNote",
)


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def reviewable_store_sha256(store: dict[str, Any]) -> str:
    reviewable = {
        "region": store.get("region"),
        "retrievedAt": store.get("retrievedAt"),
        "products": store.get("products"),
    }
    encoded = json.dumps(
        reviewable,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def is_iso_date(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    try:
        date.fromisoformat(value)
    except ValueError:
        return False
    return True


def build_review(
    studio: dict[str, Any],
    store: dict[str, Any],
    studio_path: Path,
    store_path: Path,
    audit_path: Path,
) -> dict[str, Any]:
    source_errors = validate_studio_snapshot(studio) + validate_store_snapshot(store)
    if source_errors:
        raise CatalogueValidationError("; ".join(source_errors))

    studio_by_key = {
        f"{record['fila_id']}:{record['fila_color_code']}": record
        for record in studio["data"]
    }
    products = []
    for product in store["products"]:
        variants = []
        for variant in product["variants"]:
            key = f"{variant['profileId']}:{variant['colourVariantId']}"
            studio_record = studio_by_key.get(key)
            if studio_record is None:
                raise CatalogueValidationError(f"store identity isn't present in Studio: {key}")
            variants.append(
                {
                    "key": key,
                    "name": studio_record["fila_color_name"]["en"],
                    "colours": studio_record["fila_color"],
                    "availability": variant.get(
                        "availability", product.get("availability", "active")
                    ),
                    "soldAs": variant.get("soldAs", product["soldAs"]),
                    "evidenceNote": variant.get("evidenceNote"),
                    "mappingDecision": "pending",
                    "reviewNotes": "",
                }
            )
        products.append(
            {
                "reviewKey": f"{product['materialVariant']}|{product.get('productURL') or ''}",
                "materialFamily": product["materialFamily"],
                "materialVariant": product["materialVariant"],
                "productURL": product.get("productURL"),
                "soldAs": product["soldAs"],
                "confirmedAt": product["confirmedAt"],
                "evidenceNote": product.get("evidenceNote"),
                "packagingDecision": "pending",
                "reviewNotes": "",
                "variants": variants,
            }
        )

    return {
        "schemaVersion": 1,
        "region": "AU",
        "storeSnapshot": {
            "path": str(store_path),
            "reviewableContentSHA256": reviewable_store_sha256(store),
        },
        "studioSnapshot": {
            "path": str(studio_path),
            "sha256": file_sha256(studio_path),
        },
        "collectionAudit": {
            "path": str(audit_path),
            "sha256": file_sha256(audit_path),
        },
        "reviewer": None,
        "reviewedAt": None,
        "reviewNotes": "",
        "products": products,
    }


def validate_review(
    review: dict[str, Any],
    studio: dict[str, Any],
    store: dict[str, Any],
    studio_path: Path,
    store_path: Path,
    audit_path: Path,
    require_complete: bool = False,
) -> list[str]:
    errors: list[str] = []
    try:
        expected = build_review(studio, store, studio_path, store_path, audit_path)
    except CatalogueValidationError as error:
        return [str(error)]

    if review.get("schemaVersion") != 1:
        errors.append("review schemaVersion must be 1")
    if review.get("region") != "AU":
        errors.append("review region must be AU")
    for source_name in ("studioSnapshot", "collectionAudit"):
        record = review.get(source_name)
        if not isinstance(record, dict):
            errors.append(f"review {source_name} must be an object")
        elif record.get("sha256") != expected[source_name]["sha256"]:
            errors.append(f"review {source_name} hash doesn't match its source")
    store_record = review.get("storeSnapshot")
    if not isinstance(store_record, dict):
        errors.append("review storeSnapshot must be an object")
    elif (
        store_record.get("reviewableContentSHA256")
        != expected["storeSnapshot"]["reviewableContentSHA256"]
    ):
        errors.append("review storeSnapshot content hash doesn't match its source")

    products = review.get("products")
    if not isinstance(products, list):
        return errors + ["review products must be an array"]
    if len(products) != len(expected["products"]):
        errors.append(
            f"review has {len(products)} products, expected {len(expected['products'])}"
        )

    for product_index, expected_product in enumerate(expected["products"]):
        if product_index >= len(products):
            break
        product = products[product_index]
        label = expected_product["reviewKey"]
        if not isinstance(product, dict):
            errors.append(f"review product {label} must be an object")
            continue
        for field_name in IMMUTABLE_PRODUCT_FIELDS:
            if product.get(field_name) != expected_product.get(field_name):
                errors.append(f"review product {label} changed source field {field_name}")
        packaging_decision = product.get("packagingDecision")
        if packaging_decision not in DECISIONS:
            errors.append(f"review product {label} has an invalid packagingDecision")
        elif require_complete and packaging_decision != "approved":
            errors.append(f"review product {label} packaging isn't approved")

        variants = product.get("variants")
        expected_variants = expected_product["variants"]
        if not isinstance(variants, list):
            errors.append(f"review product {label} variants must be an array")
            continue
        if len(variants) != len(expected_variants):
            errors.append(
                f"review product {label} has {len(variants)} variants, "
                f"expected {len(expected_variants)}"
            )
        for variant_index, expected_variant in enumerate(expected_variants):
            if variant_index >= len(variants):
                break
            variant = variants[variant_index]
            key = expected_variant["key"]
            if not isinstance(variant, dict):
                errors.append(f"review variant {key} must be an object")
                continue
            for field_name in IMMUTABLE_VARIANT_FIELDS:
                if variant.get(field_name) != expected_variant.get(field_name):
                    errors.append(f"review variant {key} changed source field {field_name}")
            mapping_decision = variant.get("mappingDecision")
            if mapping_decision not in DECISIONS:
                errors.append(f"review variant {key} has an invalid mappingDecision")
            elif require_complete and mapping_decision != "approved":
                errors.append(f"review variant {key} mapping isn't approved")
            if require_complete and expected_variant["availability"] in {
                "reviewNeeded",
                "unknown",
            }:
                errors.append(f"store variant {key} still has unresolved availability")

    if require_complete:
        if not isinstance(review.get("reviewer"), str) or not review["reviewer"].strip():
            errors.append("completed review needs a reviewer")
        if not is_iso_date(review.get("reviewedAt")):
            errors.append("completed review needs an ISO reviewedAt date")
        audit_text = audit_path.read_text(encoding="utf-8")
        if "Review status: approved" not in audit_text:
            errors.append("collection audit must have Review status: approved")

    return errors


def approve_store_snapshot(
    review: dict[str, Any],
    studio: dict[str, Any],
    store: dict[str, Any],
    studio_path: Path,
    store_path: Path,
    audit_path: Path,
    review_path: Path,
) -> dict[str, Any]:
    errors = validate_review(
        review,
        studio,
        store,
        studio_path,
        store_path,
        audit_path,
        require_complete=True,
    )
    if errors:
        raise CatalogueValidationError("; ".join(errors))

    approved = copy.deepcopy(store)
    old_notes = store.get("review", {}).get("notes", [])
    if not isinstance(old_notes, list):
        old_notes = []
    approved["review"] = {
        "status": "approved",
        "reviewedBy": review["reviewer"].strip(),
        "reviewedAt": review["reviewedAt"],
        "notes": old_notes,
        "signoff": {
            "path": str(review_path),
            "reviewSHA256": file_sha256(review_path),
            "collectionAuditPath": str(audit_path),
            "collectionAuditSHA256": file_sha256(audit_path),
        },
    }
    return approved


def write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="operation", required=True)
    for operation in ("prepare", "validate", "approve"):
        command = subparsers.add_parser(operation)
        command.add_argument("--studio", required=True, type=Path)
        command.add_argument("--store", required=True, type=Path)
        command.add_argument("--audit", required=True, type=Path)
        if operation == "prepare":
            command.add_argument("--output", required=True, type=Path)
        else:
            command.add_argument("--review", required=True, type=Path)
            if operation == "validate":
                command.add_argument("--require-complete", action="store_true")
            else:
                command.add_argument("--output", required=True, type=Path)
    arguments = parser.parse_args()

    try:
        studio = load_json(arguments.studio)
        store = load_json(arguments.store)
        if arguments.operation == "prepare":
            review = build_review(
                studio,
                store,
                arguments.studio,
                arguments.store,
                arguments.audit,
            )
            write_json(arguments.output, review)
            variant_count = sum(len(product["variants"]) for product in review["products"])
            print(
                f"Prepared {len(review['products'])} products and {variant_count} variants "
                f"for review in {arguments.output}."
            )
            return 0

        review = load_json(arguments.review)
        if arguments.operation == "approve":
            if arguments.output.resolve() == arguments.store.resolve():
                raise CatalogueValidationError(
                    "approved snapshot output must differ from the reviewed draft"
                )
            approved = approve_store_snapshot(
                review,
                studio,
                store,
                arguments.studio,
                arguments.store,
                arguments.audit,
                arguments.review,
            )
            write_json(arguments.output, approved)
            print(f"Wrote approved store snapshot to {arguments.output}.")
            return 0
        errors = validate_review(
            review,
            studio,
            store,
            arguments.studio,
            arguments.store,
            arguments.audit,
            arguments.require_complete,
        )
    except (CatalogueValidationError, OSError) as error:
        print(f"Store review failed: {error}", file=sys.stderr)
        return 1

    if errors:
        print("Store review failed:", file=sys.stderr)
        for error in errors:
            print(f"  - {error}", file=sys.stderr)
        return 1
    status = "complete" if arguments.require_complete else "structurally valid"
    print(f"Store review is {status}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
