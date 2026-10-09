import copy
import hashlib
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import prepare_store_review as STORE_REVIEW

MODULE_PATH = ROOT / "tools" / "check_release_readiness.py"
SPEC = importlib.util.spec_from_file_location("check_release_readiness", MODULE_PATH)
assert SPEC and SPEC.loader
READINESS = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = READINESS
SPEC.loader.exec_module(READINESS)


class ReleaseReadinessTests(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary_directory.cleanup)
        self.root = Path(self.temporary_directory.name)

        self.studio = {
            "sourceRevision": "a" * 40,
            "sourceDocumentSHA256": "b" * 64,
            "retrievedAt": "2026-10-02",
            "data": [
                {
                    "fila_id": "GFA00",
                    "fila_color_code": "10300",
                    "fila_color_type": "single",
                    "fila_type": "PLA Basic",
                    "fila_color_name": {"en": "Orange"},
                    "color_code": "A0",
                    "fila_color": ["#FF6A13FF"],
                }
            ],
        }
        self.store = {
            "region": "AU",
            "retrievedAt": "2026-10-03",
            "review": {"status": "draft", "notes": []},
            "products": [
                {
                    "materialFamily": "PLA",
                    "materialVariant": "PLA Basic",
                    "productURL": "https://au.store.bambulab.com/products/pla-basic-filament",
                    "soldAs": "both",
                    "confirmedAt": "2026-10-03",
                    "variants": [{"profileId": "GFA00", "colourVariantId": "10300"}],
                }
            ],
        }
        self.overrides = {"entries": {}}
        self.previous = {
            "schemaVersion": 1,
            "catalogueVersion": "2026.10.02.1-prototype",
            "region": "AU",
            "entryCount": 0,
            "entries": [],
        }
        self.catalogue = {
            "schemaVersion": 1,
            "catalogueVersion": "2026.10.03.1",
            "generatedAt": "2026-10-03T00:00:00Z",
            "region": "AU",
            "generatorVersion": "0.3.0",
            "sourceStudioRevision": "a" * 40,
            "sourceRetrievalDates": {
                "bambuStudio": "2026-10-02",
                "australianStore": "2026-10-03",
            },
            "entryCount": 1,
            "contentChecksum": None,
            "entries": [
                {
                    "key": "GFA00:10300",
                    "manufacturer": "Bambu Lab",
                    "profileId": "GFA00",
                    "colourVariantId": "10300",
                    "colourCode": "A0",
                    "materialFamily": "PLA",
                    "materialVariant": "PLA Basic",
                    "name": "Orange",
                    "alternateNames": [],
                    "swatchType": "solid",
                    "colours": ["#FF6A13FF"],
                    "availability": "active",
                    "soldAs": "both",
                    "productURL": "https://au.store.bambulab.com/products/pla-basic-filament",
                    "firstSeen": "2026.10.03.1",
                    "lastSeenActive": "2026-10-03",
                    "sourceEvidence": {
                        "studioPath": "filaments_color_codes.json#GFA00:10300",
                        "australianStoreURL": "https://au.store.bambulab.com/products/pla-basic-filament",
                        "note": None,
                    },
                }
            ],
        }
        self.paths = {
            "studio": self.write_json("studio.json", self.studio),
            "store": self.write_json("store.json", self.store),
            "overrides": self.write_json("overrides.json", self.overrides),
            "previous": self.write_json("previous.json", self.previous),
            "catalogue": self.write_json("catalogue.json", self.catalogue),
        }
        self.paths["audit"] = self.root / "collection-audit.md"
        self.paths["audit"].write_text("Review status: approved\n", encoding="utf-8")
        self.store_review = STORE_REVIEW.build_review(
            self.studio,
            self.store,
            self.paths["studio"],
            self.paths["store"],
            self.paths["audit"],
        )
        self.store_review["reviewer"] = "Test Reviewer"
        self.store_review["reviewedAt"] = "2026-10-03"
        self.store_review["products"][0]["packagingDecision"] = "approved"
        self.store_review["products"][0]["variants"][0]["mappingDecision"] = "approved"
        self.paths["review"] = self.write_json("store-review.json", self.store_review)
        self.store = STORE_REVIEW.approve_store_snapshot(
            self.store_review,
            self.studio,
            self.store,
            self.paths["studio"],
            self.paths["store"],
            self.paths["audit"],
            self.paths["review"],
        )
        self.paths["store"] = self.write_json("store.json", self.store)
        self.manifest = {
            "catalogueVersion": "2026.10.03.1",
            "generatedAt": "2026-10-03T00:00:00Z",
            "generatorVersion": "0.3.0",
            "sourceStudioRevision": "a" * 40,
            "storeReview": copy.deepcopy(self.store["review"]),
            "inputs": {
                name: {"path": str(path), "sha256": self.sha256(path)}
                for name, path in self.paths.items()
                if name in READINESS.MANIFEST_INPUTS
            },
        }
        self.report = """# Catalogue review: 2026.10.03.1

Store snapshot review: approved

## Unmatched store variants

None.

## Warnings

None.
"""
        self.paths["report"] = self.root / "report.md"
        self.paths["report"].write_text(self.report, encoding="utf-8")
        self.manifest["outputs"] = {
            name: {"path": str(self.paths[name]), "sha256": self.sha256(self.paths[name])}
            for name in READINESS.MANIFEST_OUTPUTS
        }

    def write_json(self, name, value):
        path = self.root / name
        path.write_text(json.dumps(value), encoding="utf-8")
        return path

    @staticmethod
    def sha256(path):
        return hashlib.sha256(path.read_bytes()).hexdigest()

    def errors(self):
        return READINESS.release_readiness_errors(
            self.catalogue,
            self.previous,
            self.studio,
            self.store,
            self.overrides,
            self.manifest,
            self.store_review,
            self.report,
            self.paths,
        )

    def test_approved_consistent_release_passes(self):
        self.assertEqual([], self.errors())

    def test_draft_store_and_unresolved_entry_block_release(self):
        self.store["review"]["status"] = "draft"
        self.catalogue["entries"][0]["availability"] = "reviewNeeded"

        errors = self.errors()

        self.assertIn("store snapshot must be approved for this operation", errors)
        self.assertIn(
            "release catalogue has unresolved availability: GFA00:10300",
            errors,
        )

    def test_changed_input_hash_blocks_release(self):
        self.paths["overrides"].write_text('{"entries":{"changed":{}}}', encoding="utf-8")

        self.assertIn("manifest hash doesn't match overrides input", self.errors())

    def test_changed_generated_catalogue_blocks_release(self):
        self.paths["catalogue"].write_text("{}", encoding="utf-8")

        self.assertIn("manifest hash doesn't match catalogue output", self.errors())

    def test_changed_human_signoff_blocks_release(self):
        self.paths["review"].write_text("{}", encoding="utf-8")

        self.assertIn(
            "approved store review hash doesn't match the sign-off file",
            self.errors(),
        )

    def test_active_entry_missing_from_approved_store_blocks_release(self):
        self.store["products"][0]["variants"] = []

        self.assertIn(
            "active catalogue entries missing from the approved store snapshot: GFA00:10300",
            self.errors(),
        )

    def test_draft_version_and_incomplete_report_block_release(self):
        self.catalogue["catalogueVersion"] = "2026.10.03.1-draft"
        self.manifest["catalogueVersion"] = "2026.10.03.1-draft"
        self.report = "# Catalogue review: 2026.10.03.1-draft\n"

        errors = self.errors()

        self.assertIn("release catalogueVersion must not contain draft or prototype", errors)
        self.assertTrue(any("Store snapshot review: approved" in error for error in errors))

    def test_invalid_or_non_increasing_release_version_is_rejected(self):
        self.catalogue["catalogueVersion"] = "2026.10.02.1"
        self.manifest["catalogueVersion"] = "2026.10.02.1"

        self.assertIn(
            "release catalogueVersion must be newer than the previous catalogue",
            self.errors(),
        )

        self.catalogue["catalogueVersion"] = "2026.13.01.1"
        self.manifest["catalogueVersion"] = "2026.13.01.1"
        self.assertIn("release catalogueVersion must use YYYY.MM.DD.N", self.errors())


if __name__ == "__main__":
    unittest.main()
