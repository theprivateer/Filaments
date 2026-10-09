import copy
import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
MODULE_PATH = ROOT / "tools" / "validate_catalogue_sources.py"
SPEC = importlib.util.spec_from_file_location("validate_catalogue_sources", MODULE_PATH)
assert SPEC and SPEC.loader
SOURCES = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = SOURCES
SPEC.loader.exec_module(SOURCES)


class CatalogueSourceValidatorTests(unittest.TestCase):
    def setUp(self):
        self.studio = {
            "sourceRevision": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
            "sourceDocumentSHA256": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
            "retrievedAt": "2026-10-02",
            "data": [
                {
                    "fila_id": "GFA00",
                    "fila_color_code": "10300",
                    "fila_color_type": "单色",
                    "fila_type": "PLA Basic",
                    "fila_color_name": {"en": "Orange"},
                    "color_code": "A0",
                    "fila_color": ["#FF6A13FF"],
                }
            ],
        }
        self.store = {
            "region": "AU",
            "retrievedAt": "2026-10-02",
            "review": {"status": "draft"},
            "products": [
                {
                    "materialFamily": "PLA",
                    "materialVariant": "PLA Basic",
                    "productURL": "https://au.store.bambulab.com/products/pla-basic-filament",
                    "soldAs": "both",
                    "confirmedAt": "2026-10-02",
                    "variants": [
                        {"profileId": "GFA00", "colourVariantId": "10300"}
                    ],
                }
            ],
        }

    def test_valid_draft_sources_pass(self):
        self.assertEqual([], SOURCES.validate_studio_snapshot(self.studio))
        self.assertEqual([], SOURCES.validate_store_snapshot(self.store))

    def test_approved_store_snapshot_needs_reviewer_and_date(self):
        self.store["review"] = {"status": "approved"}
        errors = SOURCES.validate_store_snapshot(self.store)
        self.assertIn("approved store snapshots need review.reviewedBy", errors)
        self.assertIn("approved store snapshots need an ISO review.reviewedAt date", errors)
        self.assertIn("approved store snapshots need review.signoff", errors)

    def test_release_operation_rejects_draft_snapshot(self):
        errors = SOURCES.validate_store_snapshot(self.store, require_approved=True)
        self.assertIn("store snapshot must be approved for this operation", errors)

    def test_invalid_studio_colour_is_rejected(self):
        self.studio["data"][0]["fila_color"] = ["#FF6A13"]
        errors = SOURCES.validate_studio_snapshot(self.studio)
        self.assertIn("Studio data[0].fila_color values must use #RRGGBBAA", errors)

    def test_studio_revision_must_be_a_pinned_commit(self):
        self.studio["sourceRevision"] = "master"
        errors = SOURCES.validate_studio_snapshot(self.studio)
        self.assertIn(
            "Studio sourceRevision must be a 40-character lowercase Git commit",
            errors,
        )

    def test_studio_source_document_hash_is_required(self):
        self.studio["sourceDocumentSHA256"] = "not-a-hash"
        errors = SOURCES.validate_studio_snapshot(self.studio)
        self.assertIn(
            "Studio sourceDocumentSHA256 must be a lowercase SHA-256 digest",
            errors,
        )

    def test_duplicate_store_mapping_is_rejected(self):
        duplicate = copy.deepcopy(self.store["products"][0]["variants"][0])
        self.store["products"][0]["variants"].append(duplicate)
        errors = SOURCES.validate_store_snapshot(self.store)
        self.assertIn("store identity is mapped more than once: GFA00:10300", errors)


if __name__ == "__main__":
    unittest.main()
