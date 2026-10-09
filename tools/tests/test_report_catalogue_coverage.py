import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
MODULE_PATH = ROOT / "tools" / "report_catalogue_coverage.py"
SPEC = importlib.util.spec_from_file_location("report_catalogue_coverage", MODULE_PATH)
assert SPEC and SPEC.loader
COVERAGE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = COVERAGE
SPEC.loader.exec_module(COVERAGE)


class CatalogueCoverageReportTests(unittest.TestCase):
    def setUp(self):
        self.studio = {
            "sourceRevision": "a" * 40,
            "sourceDocumentSHA256": "b" * 64,
            "retrievedAt": "2026-10-02",
            "data": [
                self.record("GFA00", "10300", "PLA Basic", "Orange"),
                self.record("GFA00", "10900", "PLA Basic", "Arctic Whisper"),
                self.record("GFG02", "33102", "PETG HF", "Black"),
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

    @staticmethod
    def record(profile_id, variant_id, material_type, name):
        return {
            "fila_id": profile_id,
            "fila_color_code": variant_id,
            "fila_color_type": "单色",
            "fila_type": material_type,
            "fila_color_name": {"en": name},
            "color_code": "A0",
            "fila_color": ["#FFFFFFFF"],
        }

    def test_report_separates_studio_counts_from_au_mappings(self):
        report = COVERAGE.render_coverage(self.studio, self.store)
        self.assertIn("Studio records: 3", report)
        self.assertIn("Australian colour mappings: 1", report)
        self.assertIn("| PLA Basic | 2 | 1 |", report)
        self.assertIn("| PETG HF | 1 | 0 |", report)
        self.assertIn("not proof of current Australian sale", report)
        self.assertIn(
            "## Studio-only identities in partially mapped material types", report
        )
        self.assertIn("### PLA Basic", report)
        self.assertIn("- `GFA00:10900` Arctic Whisper", report)
        self.assertNotIn("- `GFG02:33102` Black", report)
        self.assertIn("aren't evidence of current Australian sale or discontinuation", report)

    def test_unmatched_store_key_is_reported(self):
        self.store["products"][0]["variants"][0] = {
            "profileId": "UNKNOWN",
            "colourVariantId": "99999",
        }
        report = COVERAGE.render_coverage(self.studio, self.store)
        self.assertIn("`UNKNOWN:99999`", report)


if __name__ == "__main__":
    unittest.main()
