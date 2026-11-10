import tempfile
import unittest
from pathlib import Path

from tests.helpers import ROOT
from tollgate_analysis import tomlout
from tollgate_core import config, fragments

GOOD = '''[profile]
paths = ["**/ai/**", "**/llm/**"]
min_level = "L1"
agent = "tollgate:implementer-ai"
reviewer = "tollgate:reviewer-ai"
skills = []

[detect]
content = ["from anthropic import", "api.openai.com"]
'''


class FragmentsTest(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        self.dir = self.root / "templates" / "profiles"

    @staticmethod
    def q(s):
        return tomlout.table("x", {"v": s}).splitlines()[-1].split(" = ", 1)[1]

    def put(self, name, text):
        self.dir.mkdir(parents=True, exist_ok=True)
        (self.dir / name).write_text(text, encoding="utf-8")

    def skill(self, area, text):
        d = self.root / "skills" / f"rules-{area}"
        d.mkdir(parents=True, exist_ok=True)
        (d / "SKILL.md").write_text(text, encoding="utf-8")

    def test_load_reads_profile_and_detect(self):
        self.put("zeta.toml", GOOD)
        self.put("ai.toml", GOOD)
        self.put("note.txt", "ignorato")
        frs = fragments.load(self.root)
        self.assertEqual([f.area for f in frs], ["ai", "zeta"])
        f = frs[0]
        self.assertEqual(f.profile["min_level"], "L1")
        self.assertEqual(f.profile["paths"], ["**/ai/**", "**/llm/**"])
        self.assertEqual(f.detect, ("from anthropic import", "api.openai.com"))
        self.assertEqual(f.skill_path, self.root / "skills" / "rules-ai" / "SKILL.md")
        self.assertEqual(f.source, self.dir / "ai.toml")

    def test_load_rejects_wrong_value_types(self):
        for line in ("paths = \"x\"", "min_level = 1", "skills = [1]", "min_level = \"L9\"", "agent = 3"):
            with self.subTest(line=line):
                body = line if line.startswith("paths") else f'paths = ["**/ai/**"]\n{line}'
                self.put("ai.toml", f"[profile]\n{body}\n")
                with self.assertRaises(fragments.FragmentError) as cm:
                    fragments.load(self.root)
                self.assertIn("ai.toml", str(cm.exception))

    def test_load_missing_dir_is_empty(self):
        self.assertEqual(fragments.load(self.root), [])

    def test_load_without_detect_is_empty_tuple(self):
        self.put("ai.toml", '[profile]\npaths = ["**/ai/**"]\n')
        self.assertEqual(fragments.load(self.root)[0].detect, ())

    def test_load_rejects_unknown_key(self):
        self.put("ai.toml", '[profile]\nbogus = "x"\n')
        with self.assertRaises(fragments.FragmentError) as cm:
            fragments.load(self.root)
        self.assertIn("ai.toml", str(cm.exception))

    def test_load_rejects_rules_in_fragment(self):
        for key in ("rules", "blocking_rules"):
            with self.subTest(key=key):
                self.put("ai.toml", f'[profile]\n{key} = ["R-AI-01"]\n')
                with self.assertRaises(fragments.FragmentError):
                    fragments.load(self.root)

    def test_load_rejects_reserved_and_invalid_names(self):
        for name in ("base.toml", "active.toml", "Ai.toml", "a_b.toml", "a b.toml"):
            with self.subTest(name=name):
                for old in self.dir.glob("*.toml") if self.dir.exists() else []:
                    old.unlink()
                self.put(name, GOOD)
                with self.assertRaises(fragments.FragmentError) as cm:
                    fragments.load(self.root)
                self.assertIn(name, str(cm.exception))

    def test_load_rejects_other_pattern_forms(self):
        for pat in ("**/*.sql", "src/ai/**", "**/a/b/**", "**/**", "!**/ai/**",
                    "**/a*/**", ""):
            with self.subTest(pat=pat):
                self.put("ai.toml", f'[profile]\npaths = [{self.q(pat)}]\n')
                with self.assertRaises(fragments.FragmentError):
                    fragments.load(self.root)

    def test_load_rejects_missing_or_empty_paths(self):
        for text in ('[profile]\nmin_level = "L1"\n', '[profile]\npaths = []\n', ''):
            with self.subTest(text=text):
                self.put("ai.toml", text)
                with self.assertRaises(fragments.FragmentError) as cm:
                    fragments.load(self.root)
                self.assertIn("ai.toml", str(cm.exception))

    def test_load_rejects_dot_folders(self):
        for pat in ("**/./**", "**/../**"):
            with self.subTest(pat=pat):
                self.put("ai.toml", f'[profile]\npaths = [{self.q(pat)}]\n')
                with self.assertRaises(fragments.FragmentError):
                    fragments.load(self.root)

    def test_load_rejects_unreadable(self):
        self.put("ai.toml", "[profile\nnon valido")
        with self.assertRaises(fragments.FragmentError) as cm:
            fragments.load(self.root)
        self.assertIn("ai.toml", str(cm.exception))

    def test_load_rejects_bad_shape(self):
        for text in ('[other]\nx = 1\n', '[detect]\ncontent = "x"\n',
                     '[detect]\ncontent = [1]\n', '[detect]\nother = []\n', 'profile = 3\n'):
            with self.subTest(text=text):
                self.put("ai.toml", text)
                with self.assertRaises(fragments.FragmentError):
                    fragments.load(self.root)

    def test_exclude_parsed(self):
        self.put("ai.toml", '[profile]\npaths = ["**/ai/**"]\n'
                            '[detect]\nexclude = ["supabase/", "a/b/"]\n')
        self.assertEqual(fragments.load(self.root)[0].exclude, ("supabase/", "a/b/"))
        self.put("ai.toml", GOOD)
        self.assertEqual(fragments.load(self.root)[0].exclude, ())

    def test_exclude_rejects_bad_forms(self):
        for value in ('["supabase"]', '["/supabase/"]', '["supa*/"]', '["../x/"]', '["./x/"]',
                      '["a//b/"]', '[""]', '3', '[1]', '"supabase/"'):
            with self.subTest(value=value):
                self.put("ai.toml", f'[profile]\npaths = ["**/ai/**"]\n[detect]\nexclude = {value}\n')
                with self.assertRaises(fragments.FragmentError) as cm:
                    fragments.load(self.root)
                self.assertIn("ai.toml", str(cm.exception))
                self.assertIn("exclude", str(cm.exception))
                self.assertNotIn("sconosciuta", str(cm.exception))

    def test_detect_unknown_key_still_rejected(self):
        self.put("ai.toml", '[profile]\npaths = ["**/ai/**"]\n[detect]\nother = []\n')
        with self.assertRaises(fragments.FragmentError) as cm:
            fragments.load(self.root)
        self.assertIn("ai.toml", str(cm.exception))
        self.assertIn("sconosciuta", str(cm.exception))

    def test_approved_needs_approved_skill(self):
        self.put("ai.toml", GOOD)
        f = fragments.load(self.root)[0]
        self.assertFalse(fragments.approved(f))
        self.skill("ai", "---\nname: rules-ai\n---\nR-AI-01 x\n")
        self.assertFalse(fragments.approved(f))
        self.skill("ai", "---\nname: rules-ai\napproved: 2026-11-01\n---\nR-AI-01 x\n")
        self.assertTrue(fragments.approved(f))

    def test_rules_from_skill(self):
        self.put("ai.toml", GOOD)
        f = fragments.load(self.root)[0]
        with self.assertRaises(fragments.FragmentError):
            fragments.rules(f)
        self.skill("ai", "---\nname: rules-ai\n---\nR-AI-02 b\nR-AI-01 [blocca] a\n")
        self.assertEqual(fragments.rules(f), (["R-AI-01", "R-AI-02"], ["R-AI-01"]))

    def test_parse_pattern_forms(self):
        P = fragments.Pattern
        for pat, want in (("**/ai/**", P("folder", "ai")), ("infra/**", P("root_folder", "infra")),
                          ("**/vercel.json", P("name", "vercel.json")),
                          ("**/Dockerfile*", P("name", "Dockerfile*")),
                          ("**/.dockerignore", P("name", ".dockerignore")),
                          ("**/ai", P("name", "ai")), ("**/ab*", P("name", "ab*"))):
            with self.subTest(pat=pat):
                self.assertEqual(fragments.parse_pattern(pat), want)

    def test_parse_pattern_rejects(self):
        for pat in ("**/*", "**/**", "**", "**/*.sql", "**/*.json", "**/*.Dockerfile", "**/a*b",
                    "**/a*", "**/Dockerfile**", "**/x", "**/a/b", "src/x/**", "/infra/**",
                    "vercel.json", "**/.", "**/..", "**/./**", "**/a?b", "**/a[b]", "**/a\\b",
                    "!**/x/**", "**/*.{tsx,jsx}", "**/", "**/ x", "**/\u00e8.json", "**/a*/**"):
            with self.subTest(pat=pat):
                self.assertIsNone(fragments.parse_pattern(pat))

    def test_load_accepts_three_forms(self):
        self.put("infra.toml", '[profile]\npaths = ["**/ai/**", "infra/**", "**/vercel.json"]\n')
        (f,) = fragments.load(self.root)
        P = fragments.Pattern
        self.assertEqual(f.patterns, (P("folder", "ai"), P("root_folder", "infra"),
                                      P("name", "vercel.json")))

    def test_load_approved_filters_unapproved(self):
        self.put("ai.toml", GOOD)
        self.put("zeta.toml", GOOD)
        self.skill("zeta", "---\nname: rules-zeta\napproved: 2026-11-01\n---\nR-ZETA-01 x\n")
        self.assertEqual([f.area for f in fragments.load_approved(self.root)], ["zeta"])

    def test_rules_unreadable_skill_raises(self):
        self.put("ai.toml", GOOD)
        f = fragments.load(self.root)[0]
        with self.assertRaises(fragments.FragmentError) as cm:
            fragments.rules(f)
        self.assertIn("rules-ai/SKILL.md", str(cm.exception))

    def test_fragment_profile_validates(self):
        self.put("ai.toml", GOOD)
        self.skill("ai", "---\nname: rules-ai\napproved: 2026-11-01\n---\n"
                         "R-AI-01 [blocca] a\nR-AI-02 b\n")
        f = fragments.load(self.root)[0]
        known, blocking = fragments.rules(f)
        profile = dict(f.profile, rules=known, blocking_rules=blocking)
        text = ('schema_version = 1\n\n[gate]\nmode = "protected"\n\n'
                + tomlout.table("profiles.ai", profile))
        cfg = config.load_config_text(text)
        self.assertEqual(cfg.warnings, [])
        self.assertEqual(cfg.get("profiles.ai.rules"), ["R-AI-01", "R-AI-02"])


class RealFragmentsTest(unittest.TestCase):
    """I frammenti veri del plugin (`templates/profiles/`)."""

    def test_real_fragments_load(self):
        found = {f.area: f for f in fragments.load(ROOT)}
        self.assertIn("ai", found)
        self.assertEqual(found["ai"].profile["agent"], "tollgate:implementer-ai")
        self.assertTrue(found["ai"].detect)
        self.assertIn("infra", found)
        self.assertEqual(found["infra"].profile["agent"], "tollgate:implementer-infra")
        self.assertFalse(found["infra"].detect)
        self.assertIn("backend", found)
        self.assertEqual(found["backend"].profile["agent"], "tollgate:implementer-backend")
        self.assertTrue(found["backend"].detect)
        self.assertEqual(found["backend"].exclude, ("supabase/",))

    def test_real_ai_fragment_approved(self):
        found = {f.area: f for f in fragments.load(ROOT)}
        self.assertTrue(fragments.approved(found["ai"]))

    def test_real_infra_fragment_approved(self):
        found = {f.area: f for f in fragments.load(ROOT)}
        self.assertTrue(fragments.approved(found["infra"]))

    def test_real_backend_fragment_approved(self):
        found = {f.area: f for f in fragments.load(ROOT)}
        self.assertTrue(fragments.approved(found["backend"]))


if __name__ == "__main__":
    unittest.main()
