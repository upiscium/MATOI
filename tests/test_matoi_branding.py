"""MATOI naming and Huroshiki compatibility regressions."""

from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from huroshiki_paths import resolve_root
from huroshiki_version import VERSION


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "shared" / "scripts"


class MatoIBrandingTest(unittest.TestCase):
    def test_new_and_legacy_entrypoints_share_source_version(self) -> None:
        for script, expected in (
            ("matoi.py", f"matoi {VERSION}"),
            ("huroshiki.py", f"huroshiki {VERSION}"),
            ("packctl.py", f"packctl {VERSION}"),
        ):
            with self.subTest(script=script):
                completed = subprocess.run(
                    [sys.executable, str(SCRIPTS / script), "--version"],
                    cwd=ROOT,
                    env={**os.environ, "PYTHONPATH": str(SCRIPTS)},
                    capture_output=True,
                    text=True,
                    check=False,
                )
                self.assertEqual(completed.returncode, 0, completed.stderr)
                self.assertEqual(completed.stdout.strip(), expected)

    def test_both_tui_entrypoints_accept_same_root_flag(self) -> None:
        for script in ("matoi.py", "huroshiki.py"):
            with self.subTest(script=script):
                completed = subprocess.run(
                    [sys.executable, str(SCRIPTS / script), "--root", "/tmp", "--help"],
                    cwd=ROOT,
                    env={**os.environ, "PYTHONPATH": str(SCRIPTS)},
                    capture_output=True,
                    text=True,
                    check=False,
                )
                self.assertEqual(completed.returncode, 0, completed.stderr)
                self.assertIn("--root PATH", completed.stdout)
                self.assertIn("HUROSHIKI_ROOT", completed.stdout)

    def test_root_resolution_preserves_legacy_environment_precedence(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            cwd = Path(temporary)
            env = {"HUROSHIKI_ROOT": "existing-packs"}
            self.assertEqual(resolve_root(environ=env, cwd=cwd), cwd / "existing-packs")
            self.assertEqual(
                resolve_root("specified-packs", environ=env, cwd=cwd),
                cwd / "specified-packs",
            )
            self.assertEqual(resolve_root(environ={}, cwd=cwd), cwd)

    def test_flake_exports_new_and_legacy_names(self) -> None:
        flake = (ROOT / "flake.nix").read_text(encoding="utf-8")
        self.assertIn('pname = "matoi";', flake)
        self.assertIn('matoi = (perSystem system).huroshiki;', flake)
        self.assertIn('huroshiki = (perSystem system).huroshiki;', flake)
        self.assertIn('"$out/bin/matoi"', flake)
        self.assertIn('"$out/bin/huroshiki"', flake)
        self.assertIn('bin/matoi', flake)
        self.assertIn('bin/packctl', flake)
        self.assertIn('completions/zsh/_matoi', flake)

    def test_completion_reuses_legacy_project_selection(self) -> None:
        completion = (ROOT / "shared/completions/zsh/_matoi").read_text(encoding="utf-8")
        self.assertTrue(completion.startswith("#compdef matoi"))
        self.assertIn('autoload -Uz +X _huroshiki', completion)
        self.assertIn('_huroshiki "$@"', completion)

    def test_legacy_stored_metadata_namespace_remains_supported(self) -> None:
        paths = (SCRIPTS / "huroshiki_paths.py").read_text(encoding="utf-8")
        roots = (SCRIPTS / "pack_migration_roots.py").read_text(encoding="utf-8")
        url_data = (SCRIPTS / "url_artifacts.py").read_text(encoding="utf-8")
        self.assertIn('environment.get("HUROSHIKI_ROOT")', paths)
        self.assertIn('document["huroshiki"]', roots)
        self.assertIn('document["huroshiki"]', url_data)

    def test_docs_show_brand_and_compatibility(self) -> None:
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertTrue(readme.startswith("# MATOI（纏）"))
        self.assertIn("formerly **Huroshiki**", readme)
        self.assertIn("nix run github:upiscium/MATOI", readme)
        self.assertIn("nix profile install github:upiscium/MATOI#matoi", readme)
        self.assertIn("HUROSHIKI_ROOT", readme)
        self.assertIn("stored", readme)


if __name__ == "__main__":
    unittest.main()
