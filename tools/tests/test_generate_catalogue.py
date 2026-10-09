import copy
import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
MODULE_PATH = ROOT / "tools" / "generate_catalogue.py"
SPEC = importlib.util.spec_from_file_location("generate_catalogue", MODULE_PATH)
assert SPEC and SPEC.loader
GENERATOR = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = GENERATOR
SPEC.loader.exec_module(GENERATOR)


class CatalogueGeneratorTests(unittest.TestCase):
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
                },
                {
                    "fila_id": "GFA00",
                    "fila_color_code": "10900",
                    "fila_color_type": "渐变色",
                    "fila_type": "PLA Basic",
                    "fila_color_name": {"en": "Arctic Whisper"},
                    "color_code": "M0",
                    "fila_color": ["#9CDBD9FF", "#FFFFFFFF"],
                },
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
                        {
                            "profileId": "GFA00",
                            "colourVariantId": "10300",
                            "stockStatus": "soldOut",
                        },
                        {
                            "profileId": "GFA00",
                            "colourVariantId": "10900",
                            "soldAs": "refill",
                        },
                    ],
                }
            ],
        }
        self.overrides = {"entries": {}}

    def generate(self, previous=None, version="1"):
        return GENERATOR.generate(
            self.studio,
            self.store,
            self.overrides,
            previous,
            version,
            "2026-10-02T00:00:00Z",
            "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
        )

    def test_generation_is_deterministic_and_maps_gradient(self):
        first, first_report = self.generate()
        second, second_report = self.generate()
        self.assertEqual(first, second)
        self.assertEqual(first_report, second_report)
        gradient = next(entry for entry in first["entries"] if entry["key"] == "GFA00:10900")
        self.assertEqual("gradient", gradient["swatchType"])
        self.assertEqual("refill", gradient["soldAs"])

    def test_swatch_inference_covers_multicolour_and_translucent(self):
        self.studio["data"] += [
            {
                "fila_id": "GFA05",
                "fila_color_code": "13901",
                "fila_color_type": "多拼色",
                "fila_type": "PLA Silk",
                "fila_color_name": {"en": "Gilded Rose"},
                "color_code": "R1",
                "fila_color": ["#7A1F3DFF", "#D4AF37FF"],
            },
            {
                "fila_id": "GFG01",
                "fila_color_code": "32501",
                "fila_color_type": "单色",
                "fila_type": "PETG Translucent",
                "fila_color_name": {"en": "Translucent Teal"},
                "color_code": "G1",
                "fila_color": ["#77EDD780"],
            },
        ]
        self.store["products"] += [
            {
                "materialFamily": "PLA",
                "materialVariant": "PLA Silk Multi-Color",
                "productURL": "https://au.store.bambulab.com/products/pla-silk-multi-color",
                "soldAs": "spool",
                "confirmedAt": "2026-10-02",
                "variants": [
                    {"profileId": "GFA05", "colourVariantId": "13901"},
                ],
            },
            {
                "materialFamily": "PETG",
                "materialVariant": "PETG Translucent",
                "productURL": "https://au.store.bambulab.com/products/petg-translucent",
                "soldAs": "spool",
                "confirmedAt": "2026-10-02",
                "variants": [
                    {"profileId": "GFG01", "colourVariantId": "32501"},
                ],
            },
        ]

        document, _ = self.generate()
        entries = {entry["key"]: entry for entry in document["entries"]}

        self.assertEqual("multicolour", entries["GFA05:13901"]["swatchType"])
        self.assertEqual("translucent", entries["GFG01:32501"]["swatchType"])

    def test_sold_out_variant_remains_active(self):
        document, _ = self.generate()
        orange = next(
            entry for entry in document["entries"] if entry["key"] == "GFA00:10300"
        )
        self.assertEqual("active", orange["availability"])

    def test_missing_previous_entry_is_retained_for_review(self):
        previous, _ = self.generate()
        self.store["products"][0]["variants"] = self.store["products"][0]["variants"][:1]

        document, report = self.generate(previous=previous, version="2")

        retained = next(entry for entry in document["entries"] if entry["key"] == "GFA00:10900")
        self.assertEqual("reviewNeeded", retained["availability"])
        self.assertIn("GFA00:10900", report.missing)

    def test_discontinued_override_requires_review_metadata(self):
        self.overrides = {
            "entries": {
                "GFA00:10300": {
                    "availability": "discontinued",
                    "reason": "Confirmed replacement product",
                    "source": "review fixture",
                }
            }
        }
        document, _ = self.generate()
        orange = next(
            entry for entry in document["entries"] if entry["key"] == "GFA00:10300"
        )
        self.assertEqual("discontinued", orange["availability"])
        self.assertIn("Override:", orange["sourceEvidence"]["note"])

        invalid_overrides = copy.deepcopy(self.overrides)
        del invalid_overrides["entries"]["GFA00:10300"]["source"]
        with self.assertRaises(GENERATOR.CatalogueValidationError):
            GENERATOR.generate(
                self.studio,
                self.store,
                invalid_overrides,
                None,
                "1",
                "2026-10-02T00:00:00Z",
                "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
            )

    def test_unmatched_store_variant_is_reported_without_guessing(self):
        self.store["products"][0]["variants"].append(
            {"profileId": "UNKNOWN", "colourVariantId": "99999"}
        )
        document, report = self.generate()
        self.assertEqual(2, document["entryCount"])
        self.assertEqual(["UNKNOWN:99999"], report.unmatched)

    def test_missing_product_url_warns_and_needs_review(self):
        self.store["products"][0]["productURL"] = None
        document, report = self.generate()
        orange = next(
            entry for entry in document["entries"] if entry["key"] == "GFA00:10300"
        )
        self.assertEqual("reviewNeeded", orange["availability"])
        self.assertIn(
            "GFA00:10300 has no Australian product URL and needs review",
            report.warnings,
        )

    def test_explicit_review_needed_mapping_is_reported(self):
        variant = self.store["products"][0]["variants"][0]
        variant["availability"] = "reviewNeeded"
        variant["evidenceNote"] = "Source swatches disagree."

        document, report = self.generate()

        orange = next(entry for entry in document["entries"] if entry["key"] == "GFA00:10300")
        self.assertEqual("reviewNeeded", orange["availability"])
        self.assertIn(
            "GFA00:10300 is reviewNeeded: Source swatches disagree.",
            report.warnings,
        )

    def test_duplicate_studio_identity_is_rejected(self):
        self.studio["data"].append(copy.deepcopy(self.studio["data"][0]))
        with self.assertRaises(GENERATOR.CatalogueValidationError):
            self.generate()

    def test_store_snapshot_needs_review_metadata(self):
        del self.store["review"]
        with self.assertRaises(GENERATOR.CatalogueValidationError):
            self.generate()

    def test_studio_revision_mismatch_is_rejected(self):
        with self.assertRaisesRegex(
            GENERATOR.CatalogueValidationError,
            "Studio snapshot revision doesn't match",
        ):
            GENERATOR.generate(
                self.studio,
                self.store,
                self.overrides,
                None,
                "1",
                "2026-10-02T00:00:00Z",
                "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
            )


if __name__ == "__main__":
    unittest.main()
