import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
MODULE_PATH = ROOT / "tools" / "validate_runtime_policy.py"
SPEC = importlib.util.spec_from_file_location("validate_runtime_policy", MODULE_PATH)
assert SPEC and SPEC.loader
POLICY = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = POLICY
SPEC.loader.exec_module(POLICY)


class RuntimePolicyTests(unittest.TestCase):
    def test_current_app_target_has_no_runtime_networking_code(self):
        self.assertEqual([], POLICY.validate_source_tree(ROOT / "Filaments"))

    def test_url_session_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "Client.swift").write_text(
                "let session = URLSession.shared\n",
                encoding="utf-8",
            )

            errors = POLICY.validate_source_tree(root)

        self.assertTrue(any("URLSession isn't allowed" in error for error in errors))

    def test_network_framework_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "Connection.swift").write_text(
                "import Network\nlet connection: NWConnection? = nil\n",
                encoding="utf-8",
            )

            errors = POLICY.validate_source_tree(root)

        self.assertTrue(any("Network framework import" in error for error in errors))
        self.assertTrue(any("Network.framework type" in error for error in errors))

    def test_external_swiftui_link_is_allowed(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "ProductLink.swift").write_text(
                'Link("Product", destination: URL(string: "https://example.com")!)\n',
                encoding="utf-8",
            )

            self.assertEqual([], POLICY.validate_source_tree(root))


if __name__ == "__main__":
    unittest.main()
