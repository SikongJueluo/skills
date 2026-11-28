import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts import skill_package


class SkillPackageTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.source = self.root / "src" / "sample"
        self.runtime = self.root / "skills" / "sample"
        self.lock = self.root / "compiler" / "lock.json"
        self.lock.parent.mkdir()
        self.write(self.source / "SPEC.zh.md", "中文规格")
        self.write(self.runtime / "SKILL.md", "English Skill")
        patches = patch.multiple(
            skill_package,
            ROOT=self.root,
            SOURCE_ROOT=self.source.parent,
            SKILLS_ROOT=self.runtime.parent,
            LOCK_PATH=self.lock,
        )
        patches.start()
        self.addCleanup(patches.stop)

    @staticmethod
    def write(path: Path, content: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    def test_static_sync_preserves_translations_and_existing_evals(self):
        script = self.source / "scripts/check.py"
        self.write(script, "print('ok')")
        script.chmod(0o755)
        self.write(self.source / "references/guide.zh.md", "中文指南")
        self.write(self.source / "references/vendor.md", "vendor reference")
        self.write(self.runtime / "references/guide.md", "English guide")
        self.write(self.source / "evals/cases.json", "source cases")
        self.write(self.runtime / "evals/cases.json", "existing cases")

        skill_package.sync([self.source])

        copied_script = self.runtime / "scripts/check.py"
        self.assertEqual(copied_script.read_bytes(), script.read_bytes())
        self.assertEqual(copied_script.stat().st_mode & 0o777, 0o755)
        self.assertEqual((self.runtime / "references/vendor.md").read_text(), "vendor reference")
        self.assertEqual((self.runtime / "references/guide.md").read_text(), "English guide")
        self.assertEqual((self.runtime / "SKILL.md").read_text(), "English Skill")
        self.assertEqual((self.runtime / "evals/cases.json").read_text(), "existing cases")
        self.assertFalse(list(self.runtime.rglob("*.zh.md")))

    def test_record_and_check_detect_changes_to_either_language(self):
        self.write(self.source / "references/guide.zh.md", "中文指南")
        self.write(self.runtime / "references/guide.md", "English guide")
        self.assertEqual(skill_package.record(self.source, "deepseek/test-id"), [])
        self.assertEqual(skill_package.check([self.source]), [])
        entry = json.loads(self.lock.read_text())["skills"]["sample"]
        self.assertEqual(entry["generator"], "deepseek/test-id")
        self.assertEqual(set(entry["translations"]), {"SKILL.md", "references/guide.md"})
        self.assertEqual(set(entry["translations"]["SKILL.md"]), {"source_sha256", "output_sha256"})

        self.write(self.source / "SPEC.zh.md", "新规格")
        self.write(self.runtime / "references/guide.md", "Changed guide")
        problems = skill_package.check([self.source])
        self.assertIn("Missing or stale translation record: sample/SKILL.md", problems)
        self.assertIn("Missing or stale translation record: sample/references/guide.md", problems)

    def test_missing_translation_and_unpaired_runtime_file_fail(self):
        self.write(self.source / "references/guide.zh.md", "中文指南")
        self.write(self.runtime / "orphan.md", "unpaired")
        self.write(self.runtime / "draft.zh.md", "不分发")
        problems = skill_package.record(self.source, "deepseek/test-id")
        self.assertIn("Missing English output: skills/sample/references/guide.md", problems)
        self.assertIn("Unpaired runtime file: skills/sample/orphan.md", problems)
        self.assertIn("Unpaired runtime file: skills/sample/draft.zh.md", problems)
        self.assertFalse(self.lock.exists())

    def test_asset_drift_fails_until_synced(self):
        self.write(self.source / "script.py", "hello")
        skill_package.sync([self.source])
        self.assertEqual(skill_package.record(self.source, "deepseek/test-id"), [])
        self.write(self.runtime / "script.py", "stale")
        self.assertIn("Missing or stale runtime asset: skills/sample/script.py; run skill-sync", skill_package.check([self.source]))
        skill_package.sync([self.source])
        self.assertEqual(skill_package.check([self.source]), [])

    def test_check_excludes_only_declared_aliases_from_source_requirement(self):
        self.write(self.runtime.parent / "jj-desc/SKILL.md", "delegate")
        self.write(self.runtime.parent / "orphan/SKILL.md", "orphan")
        self.write(self.runtime.parent / "teach-me/SKILL.md", "removed alias")
        self.write(self.runtime.parent / "teaching/SKILL.md", "removed skill")
        self.assertEqual(skill_package.record(self.source, "deepseek/test-id"), [])
        self.assertEqual(
            skill_package.check([self.source]),
            [
                "Runtime package has no source: skills/orphan",
                "Runtime package has no source: skills/teach-me",
                "Runtime package has no source: skills/teaching",
            ],
        )

    def test_static_source_cannot_overwrite_entrypoint_or_translation(self):
        for relative in ("SKILL.md", "references/guide.md"):
            with self.subTest(relative=relative):
                self.write(self.source / "references/guide.zh.md", "中文指南")
                source_asset = self.source / relative
                self.write(source_asset, "colliding asset")
                with self.assertRaisesRegex(ValueError, "collides at runtime path"):
                    skill_package.sync([self.source])
                self.assertEqual((self.runtime / "SKILL.md").read_text(), "English Skill")
                source_asset.unlink()

    def test_source_and_target_symlinks_are_not_followed(self):
        outside = self.root / "outside.txt"
        self.write(outside, "untouched")
        asset = self.source / "asset.txt"
        target = self.runtime / "asset.txt"
        asset.symlink_to(outside)
        with self.assertRaisesRegex(ValueError, "contains a symlink"):
            skill_package.sync([self.source])
        asset.unlink()
        self.write(asset, "ordinary asset")
        target.symlink_to(outside)
        with self.assertRaisesRegex(ValueError, "contains a symlink"):
            skill_package.sync([self.source])
        self.assertEqual(outside.read_text(), "untouched")

    def test_english_duplicate_in_source_is_rejected(self):
        self.write(self.source / "SKILL.en.md", "duplicate")
        with self.assertRaisesRegex(ValueError, "Keep English outputs under skills/"):
            skill_package.sync([self.source])

    def test_sync_refuses_to_treat_a_runtime_directory_as_an_asset_file(self):
        self.write(self.source / "asset.txt", "ordinary asset")
        (self.runtime / "asset.txt").mkdir()
        with self.assertRaises(IsADirectoryError):
            skill_package.sync([self.source])
        self.assertFalse((self.runtime / "asset.txt" / "asset.txt").exists())


if __name__ == "__main__":
    unittest.main()
