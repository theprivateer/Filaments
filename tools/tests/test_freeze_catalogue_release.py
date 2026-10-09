import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
MODULE_PATH = ROOT / "tools" / "freeze_catalogue_release.py"
SPEC = importlib.util.spec_from_file_location("freeze_catalogue_release", MODULE_PATH)
assert SPEC and SPEC.loader
FREEZER = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = FREEZER
SPEC.loader.exec_module(FREEZER)


class CatalogueReleaseFreezerTests(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary_directory.cleanup)
        self.root = Path(self.temporary_directory.name)
        self.paths = {}
        for name in FREEZER.ARCHIVE_FILES:
            path = self.root / f"{name}.input"
            path.write_text(f"approved {name}\n", encoding="utf-8")
            self.paths[name] = path
        self.paths["previous"].write_text("previous catalogue\n", encoding="utf-8")
        self.paths["catalogue"].write_text("release catalogue\n", encoding="utf-8")
        self.bundle_target = self.root / "bundle" / "catalogue.json"
        self.bundle_target.parent.mkdir()
        self.bundle_target.write_bytes(self.paths["previous"].read_bytes())
        self.releases_root = self.root / "releases"

    def test_freeze_archives_exact_artefacts_and_updates_bundle(self):
        release_directory = FREEZER.freeze_release(
            "2026.10.03.1",
            self.paths,
            self.bundle_target,
            self.releases_root,
        )

        self.assertEqual(self.paths["catalogue"].read_bytes(), self.bundle_target.read_bytes())
        for name, archive_name in FREEZER.ARCHIVE_FILES.items():
            self.assertEqual(
                self.paths[name].read_bytes(),
                (release_directory / archive_name).read_bytes(),
            )

    def test_freeze_rejects_a_previous_catalogue_that_isnt_bundled(self):
        self.bundle_target.write_text("different catalogue\n", encoding="utf-8")

        with self.assertRaisesRegex(ValueError, "byte-for-byte identical"):
            FREEZER.freeze_release(
                "2026.10.03.1",
                self.paths,
                self.bundle_target,
                self.releases_root,
            )

        self.assertFalse((self.releases_root / "2026.10.03.1").exists())

    def test_freeze_wont_overwrite_an_existing_release(self):
        release_directory = self.releases_root / "2026.10.03.1"
        release_directory.mkdir(parents=True)

        with self.assertRaisesRegex(ValueError, "already exists"):
            FREEZER.freeze_release(
                "2026.10.03.1",
                self.paths,
                self.bundle_target,
                self.releases_root,
            )

        self.assertEqual(self.paths["previous"].read_bytes(), self.bundle_target.read_bytes())

    def test_freeze_rejects_an_unsafe_release_version(self):
        with self.assertRaisesRegex(ValueError, "must use YYYY.MM.DD.N"):
            FREEZER.freeze_release(
                "../replacement",
                self.paths,
                self.bundle_target,
                self.releases_root,
            )

        self.assertEqual(self.paths["previous"].read_bytes(), self.bundle_target.read_bytes())


if __name__ == "__main__":
    unittest.main()
