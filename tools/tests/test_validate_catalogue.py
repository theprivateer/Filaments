import copy
import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "tools" / "validate_catalogue.py"
SPEC = importlib.util.spec_from_file_location("validate_catalogue", MODULE_PATH)
assert SPEC and SPEC.loader
VALIDATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VALIDATOR)


class CatalogueValidatorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with (ROOT / "Filaments" / "Resources" / "catalogue.json").open(encoding="utf-8") as catalogue_file:
            cls.valid = json.load(catalogue_file)

    def test_prototype_catalogue_is_valid(self):
        self.assertEqual([], VALIDATOR.validate(self.valid))

    def test_duplicate_key_is_rejected(self):
        document = copy.deepcopy(self.valid)
        document["entries"].append(copy.deepcopy(document["entries"][0]))
        document["entryCount"] += 1
        self.assertTrue(any("duplicate key" in error for error in VALIDATOR.validate(document)))

    def test_gradient_requires_two_colours(self):
        document = copy.deepcopy(self.valid)
        gradient = next(entry for entry in document["entries"] if entry["swatchType"] == "gradient")
        gradient["colours"] = gradient["colours"][:1]
        self.assertTrue(any("needs at least two colours" in error for error in VALIDATOR.validate(document)))

    def test_previous_entry_cannot_be_removed(self):
        document = copy.deepcopy(self.valid)
        document["entries"].pop()
        document["entryCount"] -= 1
        self.assertTrue(any("entries removed" in error for error in VALIDATOR.validate(document, self.valid)))

    def test_active_entry_requires_store_evidence(self):
        document = copy.deepcopy(self.valid)
        active = next(entry for entry in document["entries"] if entry["availability"] == "active")
        active["sourceEvidence"]["australianStoreURL"] = None
        self.assertTrue(any("Australian store evidence" in error for error in VALIDATOR.validate(document)))

    def test_required_document_metadata_is_validated(self):
        document = copy.deepcopy(self.valid)
        document["catalogueVersion"] = ""
        document["generatedAt"] = "not-a-date"
        document["sourceStudioRevision"] = "main"
        document["sourceRetrievalDates"]["australianStore"] = "yesterday"
        document["contentChecksum"] = "short"

        errors = VALIDATOR.validate(document)

        self.assertIn("catalogueVersion must be a non-empty string", errors)
        self.assertIn("generatedAt must be an ISO timestamp", errors)
        self.assertIn(
            "sourceStudioRevision must be a 40-character lowercase Git commit",
            errors,
        )
        self.assertIn("sourceRetrievalDates.australianStore must be an ISO date", errors)
        self.assertIn("contentChecksum must be null or a lowercase SHA-256 digest", errors)

    def test_entry_provenance_and_fixed_fields_are_validated(self):
        document = copy.deepcopy(self.valid)
        entry = document["entries"][0]
        entry["manufacturer"] = "Other"
        entry["colourCode"] = ""
        entry["firstSeen"] = ""
        entry["sourceEvidence"]["studioPath"] = ""
        entry["productURL"] = "https://example.com/not-bambu"

        errors = VALIDATOR.validate(document)

        self.assertTrue(any("manufacturer must be Bambu Lab" in error for error in errors))
        self.assertTrue(any("colourCode must be a non-empty string" in error for error in errors))
        self.assertTrue(any("firstSeen must be a non-empty string" in error for error in errors))
        self.assertTrue(any("sourceEvidence.studioPath is required" in error for error in errors))
        self.assertTrue(any("productURL must be an HTTPS Bambu Lab AU store URL" in error for error in errors))

    def test_entry_key_and_collection_shapes_fail_cleanly(self):
        document = copy.deepcopy(self.valid)
        entry = document["entries"][0]
        entry["key"] = ["not", "hashable"]
        entry["alternateNames"] = ["Valid", " "]
        entry["lastSeenActive"] = "2026-02-30"
        entry["sourceEvidence"]["note"] = 42
        entry["availability"] = ["active"]
        entry["soldAs"] = {"value": "both"}
        entry["swatchType"] = ["solid"]

        errors = VALIDATOR.validate(document)

        self.assertIn("entries[0]: key must be a non-empty string", errors)
        self.assertTrue(any("alternateNames must be an array" in error for error in errors))
        self.assertTrue(any("lastSeenActive must be null or an ISO date" in error for error in errors))
        self.assertTrue(any("sourceEvidence.note must be null or a string" in error for error in errors))
        self.assertTrue(any("unknown availability" in error for error in errors))
        self.assertTrue(any("unknown soldAs" in error for error in errors))
        self.assertTrue(any("unknown swatchType" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
