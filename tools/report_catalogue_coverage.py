#!/usr/bin/env python3
"""Report Studio source records beside reviewed Australian mappings."""

from __future__ import annotations

import argparse
import sys
from collections import Counter
from pathlib import Path
from typing import Any

from validate_catalogue import CatalogueValidationError, load_json
from validate_catalogue_sources import validate_store_snapshot, validate_studio_snapshot


def stable_key(profile_id: str, colour_variant_id: str) -> str:
    return f"{profile_id}:{colour_variant_id}"


def render_coverage(studio: dict[str, Any], store: dict[str, Any]) -> str:
    errors = validate_studio_snapshot(studio) + validate_store_snapshot(store)
    if errors:
        raise CatalogueValidationError("; ".join(errors))

    studio_by_key = {
        stable_key(record["fila_id"], record["fila_color_code"]): record
        for record in studio["data"]
    }
    studio_counts = Counter(record["fila_type"] for record in studio["data"])
    mapped_counts: Counter[str] = Counter()
    unmatched_store_keys: list[str] = []
    mapped_keys: set[str] = set()

    for product in store["products"]:
        for variant in product["variants"]:
            key = stable_key(variant["profileId"], variant["colourVariantId"])
            mapped_keys.add(key)
            studio_record = studio_by_key.get(key)
            if studio_record is None:
                unmatched_store_keys.append(key)
            else:
                mapped_counts[studio_record["fila_type"]] += 1

    lines = [
        "# Studio-to-AU mapping coverage",
        "",
        f"Studio revision: `{studio['sourceRevision']}`",
        "",
        f"Studio source SHA-256: `{studio['sourceDocumentSHA256']}`",
        "",
        f"Studio records: {len(studio_by_key)}",
        "",
        f"Studio material types: {len(studio_counts)}",
        "",
        f"Australian products in snapshot: {len(store['products'])}",
        "",
        f"Australian colour mappings: {len(mapped_keys)}",
        "",
        f"Australian review status: {store['review']['status']}",
        "",
        "Studio records are possible identity matches, not proof of current Australian sale. An unmapped Studio record mustn't be treated as a missing or discontinued Australian product.",
        "",
        "| Studio material type | Studio records | AU mappings |",
        "| --- | ---: | ---: |",
    ]
    for material_type in sorted(studio_counts, key=str.casefold):
        lines.append(
            f"| {material_type} | {studio_counts[material_type]} | {mapped_counts[material_type]} |"
        )

    lines += [
        "",
        "## Studio-only identities in partially mapped material types",
        "",
        "These records are review candidates only. They aren't evidence of current Australian sale or discontinuation.",
        "",
    ]
    partially_mapped_types = {
        material_type
        for material_type, count in studio_counts.items()
        if 0 < mapped_counts[material_type] < count
    }
    studio_only_by_type: dict[str, list[tuple[str, str]]] = {
        material_type: [] for material_type in partially_mapped_types
    }
    for key, record in studio_by_key.items():
        material_type = record["fila_type"]
        if material_type in partially_mapped_types and key not in mapped_keys:
            name = record["fila_color_name"]["en"]
            studio_only_by_type[material_type].append((key, name))

    if studio_only_by_type:
        for material_type in sorted(studio_only_by_type, key=str.casefold):
            lines.append(f"### {material_type}")
            lines.append("")
            for key, name in sorted(
                studio_only_by_type[material_type],
                key=lambda item: (item[1].casefold(), item[0]),
            ):
                lines.append(f"- `{key}` {name}")
            lines.append("")
    else:
        lines += ["None.", ""]

    lines += ["", "## Store mappings missing from Studio", ""]
    if unmatched_store_keys:
        lines.extend(f"- `{key}`" for key in sorted(unmatched_store_keys))
    else:
        lines.append("None.")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--studio", required=True, type=Path)
    parser.add_argument("--store", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    arguments = parser.parse_args()

    try:
        report = render_coverage(load_json(arguments.studio), load_json(arguments.store))
    except CatalogueValidationError as error:
        print(f"Coverage report failed: {error}", file=sys.stderr)
        return 1

    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    arguments.output.write_text(report, encoding="utf-8")
    print(f"Wrote coverage report to {arguments.output}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
