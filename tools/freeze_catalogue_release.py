#!/usr/bin/env python3
"""Freeze approved catalogue artefacts and promote the catalogue into the app bundle."""

from __future__ import annotations

import argparse
import os
import shutil
import sys
import tempfile
from pathlib import Path

from check_release_readiness import release_readiness_errors, version_key
from validate_catalogue import CatalogueValidationError, load_json

ARCHIVE_FILES = {
    "catalogue": "catalogue.json",
    "manifest": "source-manifest.json",
    "report": "review-report.md",
    "studio": "studio-snapshot.json",
    "store": "au-store-snapshot.json",
    "overrides": "overrides.json",
    "previous": "previous-catalogue.json",
    "review": "store-signoff.json",
    "audit": "collection-audit.md",
}


def freeze_release(
    version: str,
    artefact_paths: dict[str, Path],
    bundle_target: Path,
    releases_root: Path,
) -> Path:
    if version_key(version, release=True) is None:
        raise ValueError("release version must use YYYY.MM.DD.N")
    release_directory = releases_root / version
    if release_directory.exists():
        raise ValueError(f"release directory already exists: {release_directory}")
    if not bundle_target.exists():
        raise ValueError(f"bundled catalogue doesn't exist: {bundle_target}")
    if bundle_target.read_bytes() != artefact_paths["previous"].read_bytes():
        raise ValueError("--previous must be byte-for-byte identical to the bundled catalogue")

    releases_root.mkdir(parents=True, exist_ok=True)
    bundle_target.parent.mkdir(parents=True, exist_ok=True)
    staging_directory = Path(
        tempfile.mkdtemp(prefix=f".{version}-", dir=releases_root)
    )
    staged_bundle_path: Path | None = None
    installed_release_directory = False

    try:
        for artefact_name, archive_name in ARCHIVE_FILES.items():
            shutil.copy2(artefact_paths[artefact_name], staging_directory / archive_name)

        with tempfile.NamedTemporaryFile(
            prefix=".catalogue-",
            suffix=".json",
            dir=bundle_target.parent,
            delete=False,
        ) as staged_bundle:
            staged_bundle.write(artefact_paths["catalogue"].read_bytes())
            staged_bundle.flush()
            os.fsync(staged_bundle.fileno())
            staged_bundle_path = Path(staged_bundle.name)

        os.replace(staging_directory, release_directory)
        installed_release_directory = True
        os.replace(staged_bundle_path, bundle_target)
        staged_bundle_path = None
    except Exception:
        if staged_bundle_path is not None:
            staged_bundle_path.unlink(missing_ok=True)
        if installed_release_directory:
            shutil.rmtree(release_directory)
        elif staging_directory.exists():
            shutil.rmtree(staging_directory)
        raise

    return release_directory


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
    parser.add_argument("--bundle-target", required=True, type=Path)
    parser.add_argument("--releases-root", required=True, type=Path)
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
        print(f"Catalogue freeze failed: {error}", file=sys.stderr)
        return 1

    paths = {
        "catalogue": arguments.catalogue,
        "previous": arguments.previous,
        "studio": arguments.studio,
        "store": arguments.store,
        "overrides": arguments.overrides,
        "manifest": arguments.manifest,
        "report": arguments.report,
        "review": arguments.review_signoff,
        "audit": arguments.collection_audit,
    }
    readiness_paths = {
        name: path
        for name, path in paths.items()
        if name in {
            "catalogue",
            "previous",
            "studio",
            "store",
            "overrides",
            "report",
            "review",
            "audit",
        }
    }
    errors = release_readiness_errors(
        catalogue,
        previous,
        studio,
        store,
        overrides,
        manifest,
        store_review,
        report_text,
        readiness_paths,
    )
    if errors:
        print("Catalogue freeze failed release readiness:", file=sys.stderr)
        for error in errors:
            print(f"  - {error}", file=sys.stderr)
        return 1

    try:
        release_directory = freeze_release(
            catalogue["catalogueVersion"],
            paths,
            arguments.bundle_target,
            arguments.releases_root,
        )
    except (OSError, ValueError) as error:
        print(f"Catalogue freeze failed: {error}", file=sys.stderr)
        return 1

    print(
        f"Froze catalogue {catalogue['catalogueVersion']} in {release_directory} "
        f"and updated {arguments.bundle_target}."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
