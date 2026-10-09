import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
MODULE_PATH = ROOT / "tools" / "prepare_studio_snapshot.py"
SPEC = importlib.util.spec_from_file_location("prepare_studio_snapshot", MODULE_PATH)
assert SPEC and SPEC.loader
PREPARE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = PREPARE
SPEC.loader.exec_module(PREPARE)


class PrepareStudioSnapshotTests(unittest.TestCase):
    def setUp(self):
        self.raw = {
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
            ]
        }
        self.revision = "a" * 40
        self.source_hash = "b" * 64

    def test_prepare_adds_metadata_without_changing_records(self):
        snapshot = PREPARE.prepare(
            self.raw,
            self.revision,
            "2026-10-02",
            self.source_hash,
        )
        self.assertEqual(self.revision, snapshot["sourceRevision"])
        self.assertEqual(self.source_hash, snapshot["sourceDocumentSHA256"])
        self.assertEqual("2026-10-02", snapshot["retrievedAt"])
        self.assertEqual(self.raw["data"], snapshot["data"])

    def test_prepare_is_deterministic(self):
        first = PREPARE.prepare(self.raw, self.revision, "2026-10-02", self.source_hash)
        second = PREPARE.prepare(self.raw, self.revision, "2026-10-02", self.source_hash)
        self.assertEqual(first, second)

    def test_prepare_rejects_unpinned_revision(self):
        with self.assertRaisesRegex(
            PREPARE.CatalogueValidationError,
            "40-character lowercase Git commit",
        ):
            PREPARE.prepare(self.raw, "master", "2026-10-02", self.source_hash)


if __name__ == "__main__":
    unittest.main()
