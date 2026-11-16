"""Validate all bundled SKILL.md files for frontmatter integrity and zero leaked secrets/private terms."""

from __future__ import annotations

import unittest
from pathlib import Path

from mcp_server.server import _parse_frontmatter

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILLS_ROOT = REPO_ROOT / "skills"

FORBIDDEN_STRINGS = [
    "CCAI_DEV2",
    "_8H1ExBwZj4hP_E3",
    "RCMAGvAf75rR2B_SuIm6tCB3FJIVd4vd",
    "diplomats",
    "1.eps",
    "dhaka",
    "bangladesh",
]


class TestSkillsValidation(unittest.TestCase):
    def test_every_skill_has_valid_frontmatter(self) -> None:
        skill_dirs = [p for p in SKILLS_ROOT.iterdir() if p.is_dir()]
        self.assertGreaterEqual(len(skill_dirs), 3)
        for skill_dir in skill_dirs:
            skill_md = skill_dir / "SKILL.md"
            self.assertTrue(skill_md.exists(), f"Missing SKILL.md in {skill_dir}")
            meta, body = _parse_frontmatter(skill_md.read_text(encoding="utf-8"))
            self.assertEqual(meta.get("name"), skill_dir.name, f"Frontmatter name mismatch in {skill_md}")
            self.assertTrue(meta.get("description"), f"Empty description in {skill_md}")
            self.assertTrue(body.strip(), f"Empty body in {skill_md}")

    def test_no_secrets_private_content_or_personal_paths_anywhere(self) -> None:
        for path in REPO_ROOT.rglob("*"):
            if not path.is_file() or ".git" in path.parts or "__pycache__" in path.parts:
                continue
            if path.name == "test_skills_validation.py":
                continue
            try:
                content = path.read_text(encoding="utf-8").lower()
            except UnicodeDecodeError:
                continue
            for forbidden in FORBIDDEN_STRINGS:
                self.assertNotIn(
                    forbidden.lower(),
                    content,
                    f"Forbidden term '{forbidden}' found in {path}",
                )


if __name__ == "__main__":
    unittest.main()
