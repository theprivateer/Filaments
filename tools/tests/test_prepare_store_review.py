import copy
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
MODULE_PATH = ROOT / "tools" / "prepare_store_review.py"
SPEC = importlib.util.spec_from_file_location("prepare_store_review", MODULE_PATH)
assert SPEC and SPEC.loader
REVIEW = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = REVIEW
SPEC.loader.exec_module(REVIEW)


class StoreReviewTests(unittest.TestCase):
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
            "review": {"status": "draft"},
            "products": [
                {
                    "materialFamily": "PLA",
                    "materialVariant": "PLA Basic",
                    "productURL": "https://au.store.bambulab.com/products/pla-basic-filament",
                    "soldAs": "both",
                    "confirmedAt": "2026-10-03",
                    "evidenceNote": "Fixture evidence",
                    "variants": [{"profileId": "GFA00", "colourVariantId": "10300"}],
                }
            ],
        }
        self.studio_path = self.write_json("studio.json", self.studio)
        self.store_path = self.write_json("store.json", self.store)
        self.audit_path = self.root / "audit.md"
        self.audit_path.write_text("Review status: draft\n", encoding="utf-8")

    def write_json(self, name, value):
        path = self.root / name
        path.write_text(json.dumps(value), encoding="utf-8")
        return path

    def build(self):
        return REVIEW.build_review(
            self.studio,
            self.store,
            self.studio_path,
            self.store_path,
            self.audit_path,
        )

    def validate(self, review, complete=False):
        return REVIEW.validate_review(
            review,
            self.studio,
            self.store,
            self.studio_path,
            self.store_path,
            self.audit_path,
            complete,
        )

    def test_build_is_deterministic_and_pending_review_is_structurally_valid(self):
        first = self.build()
        second = self.build()

        self.assertEqual(first, second)
        self.assertEqual([], self.validate(first))
        self.assertEqual("Orange", first["products"][0]["variants"][0]["name"])
        self.assertEqual("pending", first["products"][0]["packagingDecision"])

    def test_completed_review_requires_every_decision_and_reviewer(self):
        errors = self.validate(self.build(), complete=True)

        self.assertTrue(any("packaging isn't approved" in error for error in errors))
        self.assertTrue(any("mapping isn't approved" in error for error in errors))
        self.assertIn("completed review needs a reviewer", errors)
        self.assertIn("completed review needs an ISO reviewedAt date", errors)
        self.assertIn("collection audit must have Review status: approved", errors)

    def test_completed_review_passes_after_full_signoff(self):
        review = self.build()
        review["reviewer"] = "Test Reviewer"
        review["reviewedAt"] = "2026-10-03"
        review["products"][0]["packagingDecision"] = "approved"
        review["products"][0]["variants"][0]["mappingDecision"] = "approved"
        self.audit_path.write_text("Review status: approved\n", encoding="utf-8")
        review["collectionAudit"]["sha256"] = REVIEW.file_sha256(self.audit_path)

        self.assertEqual([], self.validate(review, complete=True))

    def test_approval_records_the_exact_signoff_and_audit(self):
        review = self.build()
        review["reviewer"] = "Test Reviewer"
        review["reviewedAt"] = "2026-10-03"
        review["products"][0]["packagingDecision"] = "approved"
        review["products"][0]["variants"][0]["mappingDecision"] = "approved"
        self.audit_path.write_text("Review status: approved\n", encoding="utf-8")
        review["collectionAudit"]["sha256"] = REVIEW.file_sha256(self.audit_path)
        review_path = self.write_json("review.json", review)

        approved = REVIEW.approve_store_snapshot(
            review,
            self.studio,
            self.store,
            self.studio_path,
            self.store_path,
            self.audit_path,
            review_path,
        )

        self.assertEqual("approved", approved["review"]["status"])
        self.assertEqual("Test Reviewer", approved["review"]["reviewedBy"])
        self.assertEqual(
            REVIEW.file_sha256(review_path),
            approved["review"]["signoff"]["reviewSHA256"],
        )
        self.assertEqual(
            REVIEW.reviewable_store_sha256(self.store),
            REVIEW.reviewable_store_sha256(approved),
        )

    def test_unresolved_availability_and_changed_source_block_completion(self):
        self.store["products"][0]["variants"][0]["availability"] = "reviewNeeded"
        self.store_path = self.write_json("store.json", self.store)
        review = self.build()
        review["reviewer"] = "Test Reviewer"
        review["reviewedAt"] = "2026-10-03"
        review["products"][0]["packagingDecision"] = "approved"
        review["products"][0]["variants"][0]["mappingDecision"] = "approved"
        self.audit_path.write_text("Review status: approved\n", encoding="utf-8")
        review["collectionAudit"]["sha256"] = REVIEW.file_sha256(self.audit_path)

        self.assertIn(
            "store variant GFA00:10300 still has unresolved availability",
            self.validate(review, complete=True),
        )

        stale_review = copy.deepcopy(review)
        self.store["products"][0]["soldAs"] = "spool"
        self.store_path = self.write_json("store.json", self.store)
        errors = self.validate(stale_review)
        self.assertIn("review storeSnapshot content hash doesn't match its source", errors)


if __name__ == "__main__":
    unittest.main()
