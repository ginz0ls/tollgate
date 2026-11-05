import dataclasses
import re
import unittest

from tollgate_analysis import models
from tollgate_analysis.models import ModelInfo, ModelsFormatError

PAGE = "https://esempio.invalid/modelli"


def info(provider, id, **kw):
    base = dict(family=None, stable=True, created=None, retires=None, retiring=False)
    base.update(kw)
    return ModelInfo(provider, id, **base)


def a_info(id, line="sonnet", created="2026-01-01T00:00:00Z", lifecycle="active", retires=None):
    return info("anthropic", id, family=line, stable=lifecycle == "active", created=created,
                retires=retires, retiring=lifecycle == "deprecated")


def run(provider, literals, infos, where=None):
    """Righe di `findings` per i letterali dati, con la catena completa used -> findings."""
    lits = set(literals)
    matches = models.used(lits, infos)
    where = where or {lit: "src/ai.py" for lit in lits}
    return models.findings(provider, matches, infos, lits, where=where, page=PAGE)


class LiteralsTest(unittest.TestCase):
    def test_literals_quotes_and_charset(self):
        text = ('a = "claude-x-5"\nb = \'gemini-3.6-flash\'\nc = `gpt-x`\n'
                'd = "due parole"\ne = ""\nf = "claude-x-5@20260101"\n'
                'g = "' + "a" * 200 + '"\n')
        self.assertEqual(models.literals(text), {"claude-x-5", "gemini-3.6-flash", "gpt-x"})

    def test_literals_ignore_comments_without_quotes(self):
        text = "# commento senza virgolette: claude-y-1\n# l'agente usa \"claude-x-5\"\n"
        self.assertEqual(models.literals(text), {"claude-x-5"})

    def test_literals_do_not_cross_lines(self):
        self.assertEqual(models.literals('x = "claude-x-5\ny = claude-y-1"\n'), set())


class NormalizeTest(unittest.TestCase):
    def test_normalize_strips_models_and_provider_prefix(self):
        for raw, want in (("models/gemini-3.6-flash", "gemini-3.6-flash"),
                          ("anthropic:claude-x-5", "claude-x-5"),
                          ("google:models/gemini-3.6-flash", "gemini-3.6-flash"),
                          ("openai/gpt-x", "openai/gpt-x"), ("claude-x-5", "claude-x-5")):
            self.assertEqual(models.normalize(raw), want)


class ParseTest(unittest.TestCase):
    def test_parse_anthropic(self):
        page = {"data": [
            {"id": "a-1", "line": "sonnet", "lifecycle": "active",
             "created_at": "2026-01-01T00:00:00Z", "retires_at": None},
            {"id": "a-2", "line": None, "lifecycle": "deprecated",
             "created_at": "2025-01-01T00:00:00Z", "retires_at": "2026-12-31T00:00:00Z"},
            {"id": "a-3", "lifecycle": ["active"]},
            {"lifecycle": "active"},
            "non un dizionario",
        ], "has_more": False}
        got = models.parse_pages("anthropic", [page])
        self.assertEqual(got[0], ModelInfo("anthropic", "a-1", "sonnet", True,
                                           "2026-01-01T00:00:00Z", None, False))
        self.assertEqual(got[1], ModelInfo("anthropic", "a-2", None, False,
                                           "2025-01-01T00:00:00Z", "2026-12-31T00:00:00Z", True))
        # D20: un lifecycle non stringa non è stabile e non è in ritiro; senza id si salta
        self.assertEqual([m.id for m in got], ["a-1", "a-2", "a-3"])
        self.assertFalse(got[2].stable)
        self.assertFalse(got[2].retiring)

    def test_parse_gemini_strips_models_prefix(self):
        got = models.parse_pages("gemini", [{"models": [{"name": "models/gemini-3.6-flash"},
                                                        {"name": "models/gemini-3.7-flash-preview-x"},
                                                        {"displayName": "senza nome"}]}])
        self.assertEqual([m.id for m in got], ["gemini-3.6-flash", "gemini-3.7-flash-preview-x"])
        self.assertEqual(got[0].family, "flash")
        self.assertTrue(got[0].stable)
        self.assertFalse(got[1].stable)

    def test_parse_openai_shutdown_date(self):
        got = models.parse_pages("openai", [{"data": [{"id": "gpt-x", "shutdown_date": None},
                                                     {"id": "gpt-y", "shutdown_date": "2027-02-03"}]}])
        self.assertEqual((got[0].retiring, got[0].retires), (False, None))
        self.assertEqual((got[1].retiring, got[1].retires), (True, "2027-02-03"))

    def test_parse_openrouter_expiration_date(self):
        got = models.parse_pages("openrouter", [{"data": [{"id": "a/b", "expiration_date": None},
                                                         {"id": "a/c:free", "expiration_date": "2027-02-03"}]},
                                                {"data": [{"id": "a/d"}]}])
        self.assertEqual([(m.id, m.retiring, m.retires) for m in got],
                         [("a/b", False, None), ("a/c:free", True, "2027-02-03"), ("a/d", False, None)])

    def test_parse_wrong_shape_raises(self):
        for provider, pages in [("anthropic", [{"data": "x"}]), ("openai", [{"data": {}}]),
                                ("openrouter", [{"nodata": []}]), ("gemini", [{"models": 3}]),
                                ("anthropic", ["pagina"]), ("anthropic", "non una lista"),
                                ("sconosciuto", [{"data": []}])]:
            with self.subTest(provider=provider, pages=pages):
                with self.assertRaises(ModelsFormatError):
                    models.parse_pages(provider, pages)

    def test_models_format_error_is_value_error(self):
        self.assertTrue(issubclass(ModelsFormatError, ValueError))


class UsedTest(unittest.TestCase):
    def test_used_exact_match_and_prefixes(self):
        ai = [a_info("claude-x-5")]
        gi = [info("gemini", "models/gemini-3.6-flash")]
        self.assertEqual([lit for lit, _ in models.used({"anthropic:claude-x-5"}, ai)],
                         ["anthropic:claude-x-5"])
        self.assertEqual([lit for lit, _ in models.used({"models/gemini-3.6-flash"}, gi)],
                         ["models/gemini-3.6-flash"])
        self.assertEqual([lit for lit, _ in models.used({"google:gemini-3.6-flash"}, gi)],
                         ["google:gemini-3.6-flash"])
        self.assertEqual(models.used({"claude"}, ai), [])
        self.assertEqual(models.used({"xanthropic:claude-x-5"}, ai), [])
        self.assertEqual(models.used({"gemini-cli"}, gi), [])

    def test_alias_picks_latest_dated_id(self):
        ai = [a_info("claude-x-4-5-20250101"), a_info("claude-x-4-5-20250601")]
        (lit, got), = models.used({"claude-x-4-5"}, ai)
        self.assertEqual(got.id, "claude-x-4-5-20250601")
        self.assertEqual(models.used({"claude-x-4"}, ai), [])
        self.assertEqual(models.used({"claude-x-4-5-2025"}, ai), [])

    def test_alias_and_vertex_ids_not_flagged(self):
        ai = [a_info("claude-x-4-5-20250101")]
        lines = run("anthropic", {"claude-x-4-5"}, ai)
        self.assertEqual(len(lines), 1, lines)
        self.assertIn("alias di claude-x-4-5-20250101", lines[0])
        self.assertNotIn("non è nell'elenco", lines[0])
        self.assertEqual(models.literals('m = "claude-x-4-5@20250101"'), set())
        self.assertEqual(run("anthropic", models.literals('m = "claude-x-4-5@20250101"'), ai), [])

    def test_alias_only_for_anthropic(self):
        oi = [info("openai", "gpt-x-20250101")]
        self.assertEqual(models.used({"gpt-x"}, oi), [])


class AnthropicTest(unittest.TestCase):
    def test_anthropic_newer_same_line(self):
        infos = [a_info("a-old", created="2026-01-01T00:00:00Z"),
                 a_info("a-new", created="2026-09-01T00:00:00Z"),
                 a_info("b-newer", line="opus", created="2026-10-01T00:00:00Z")]
        lines = run("anthropic", {"a-old"}, infos)
        self.assertEqual(len(lines), 1, lines)
        self.assertIn("a-new", lines[0])
        self.assertIn("esiste a-new, più recente della stessa famiglia", lines[0])
        self.assertNotIn("b-newer", lines[0])

    def test_anthropic_newer_names_only_the_newest(self):
        infos = [a_info("a-old", created="2026-01-01"), a_info("a-mid", created="2026-05-01"),
                 a_info("a-new", created="2026-09-01")]
        lines = run("anthropic", {"a-old"}, infos)
        self.assertEqual(len(lines), 1)
        self.assertIn("a-new", lines[0])
        self.assertNotIn("a-mid", lines[0])

    def test_anthropic_newer_skipped_without_line_or_epoch_date(self):
        epoch = "1970-01-01T00:00:00Z"
        newer = a_info("a-new", created="2026-09-01T00:00:00Z")
        for old in (a_info("a-old", line=None), a_info("a-old", created=epoch),
                    a_info("a-old", created=None)):
            with self.subTest(old=old):
                self.assertEqual(run("anthropic", {"a-old"}, [old, newer]), [])
        # un candidato con data all'epoca non si propone
        self.assertEqual(run("anthropic", {"a-old"}, [a_info("a-old"), a_info("a-new", created=epoch)]), [])

    def test_anthropic_deprecated_with_date(self):
        infos = [a_info("a-1", lifecycle="deprecated", retires="2026-12-31T00:00:00Z")]
        lines = run("anthropic", {"a-1"}, infos)
        self.assertEqual(len(lines), 1)
        self.assertIn("deprecato, ritiro previsto il 2026-12-31", lines[0])
        self.assertNotIn("T00", lines[0])
        undated = run("anthropic", {"a-1"}, [a_info("a-1", lifecycle="deprecated")])
        self.assertIn("deprecato, ritiro previsto il data non indicata", undated[0])

    def test_anthropic_deprecated_newer_not_from_deprecated(self):
        infos = [a_info("a-old", created="2026-01-01"),
                 a_info("a-new", created="2026-09-01", lifecycle="deprecated")]
        self.assertEqual(run("anthropic", {"a-old"}, infos), [])

    def test_anthropic_non_string_lifecycle_never_newer_nor_retiring(self):
        infos = models.parse_pages("anthropic", [{"data": [
            {"id": "a-old", "line": "s", "lifecycle": "active", "created_at": "2026-01-01"},
            {"id": "a-new", "line": "s", "lifecycle": ["active"], "created_at": "2026-09-01"},
            {"id": "a-odd", "line": "s", "lifecycle": 7, "created_at": "2026-02-01"}]}])
        self.assertEqual(run("anthropic", {"a-old", "a-odd"}, infos), [])

    def test_unknown_prefix_only_for_versioned_names(self):
        ai = [a_info("claude-x-6")]
        lines = run("anthropic", {"claude-x-5", "claude-3-opus-20240229", "claude-code",
                                  "gemini-cli", "claude"}, ai)
        text = "\n".join(lines)
        self.assertEqual(len(lines), 2, lines)
        self.assertIn("claude-x-5", text)
        self.assertIn("claude-3-opus-20240229", text)
        self.assertEqual(text.count("non è nell'elenco: ritirato o scritto male"), 2)
        self.assertNotIn("claude-code", text)

    def test_unknown_gemini_prefix(self):
        gi = [info("gemini", "gemini-3.6-flash", family="flash")]
        lines = run("gemini", {"gemini-3.1-flash", "gemini-cli", "gemini-flash-latest"}, gi)
        self.assertEqual(len(lines), 1, lines)
        self.assertIn("gemini-3.1-flash", lines[0])
        self.assertIn("non è nell'elenco", lines[0])

    def test_unknown_names_without_models_in_use_give_no_provider_lines(self):
        lines = run("anthropic", {"claude-x-5"}, [a_info("claude-x-6")])
        self.assertEqual(len(lines), 1)
        self.assertIn("non è nell'elenco", lines[0])


class GeminiTest(unittest.TestCase):
    def test_gemini_family_parse(self):
        for name, want in [("gemini-3.6-flash", ("flash", (3, 6))),
                           ("gemini-3.6-flash-lite", ("flash-lite", (3, 6))),
                           ("gemini-2.0-flash-001", ("flash", (2, 0))),
                           ("gemini-3.8-flash-tts", ("flash-tts", (3, 8))),
                           ("gemini-2.5-flash-preview-09-2025", ("flash", (2, 5))),
                           ("models/gemini-3-flash", ("flash", (3,))),
                           ("gemini-3.7-flash-preview-tts", ("flash-tts", (3, 7))),
                           ("gemini-2.5-flash-preview-tts", ("flash-tts", (2, 5))),
                           ("gemini-2.0-flash-exp-image-generation",
                            ("flash-image-generation", (2, 0))),
                           ("gemini-2.5-flash-lite-preview-06-17", ("flash-lite", (2, 5))),
                           ("gemini-flash-latest", None), ("gemini-embedding-001", None),
                           ("claude-x-5", None), ("gemini-3.6", None)]:
            with self.subTest(name=name):
                self.assertEqual(models.gemini_family(name), want)

    def gem(self, *names):
        return models.parse_pages("gemini", [{"models": [{"name": "models/" + n} for n in names]}])

    def test_gemini_newer_stable_only(self):
        gi = self.gem("gemini-3.5-flash", "gemini-3.6-flash", "gemini-3.7-flash-preview-05-2026",
                      "gemini-3.9-flash-tts", "gemini-3.7-flash-preview-tts")
        lines = run("gemini", {"gemini-3.5-flash"}, gi)
        newer = [l for l in lines if "più recente" in l]
        self.assertEqual(len(newer), 1, lines)
        self.assertIn("gemini-3.6-flash", newer[0])
        self.assertNotIn("preview", "".join(lines))
        self.assertNotIn("tts", "".join(lines))

    def test_gemini_version_numeric(self):
        gi = self.gem("gemini-3.9-flash", "gemini-3.10-flash")
        lines = run("gemini", {"gemini-3.9-flash"}, gi)
        self.assertTrue(any("esiste gemini-3.10-flash" in l for l in lines), lines)
        self.assertFalse(any("più recente" in l for l in run("gemini", {"gemini-3.10-flash"}, gi)))

    def test_gemini_shorter_version_is_older(self):
        gi = self.gem("gemini-3-flash", "gemini-3.6-flash")
        lines = run("gemini", {"gemini-3-flash"}, gi)
        self.assertTrue(any("esiste gemini-3.6-flash" in l for l in lines), lines)

    def test_gemini_preview_mode_in_use_is_not_compared_to_plain_family(self):
        gi = self.gem("gemini-2.5-flash-preview-tts", "gemini-2.5-pro-preview-tts",
                      "gemini-3-flash", "gemini-3-pro")
        lines = run("gemini", {"gemini-2.5-flash-preview-tts", "gemini-2.5-pro-preview-tts"}, gi)
        self.assertFalse(any("più recente" in l for l in lines), lines)
        gi += self.gem("gemini-3-flash-tts")
        lines = run("gemini", {"gemini-2.5-flash-preview-tts"}, gi)
        newer = [l for l in lines if "più recente" in l]
        self.assertEqual(len(newer), 1, lines)
        self.assertIn("esiste gemini-3-flash-tts", newer[0])

    def test_anthropic_empty_line_is_no_family(self):
        items = [{"id": "a-1", "line": "", "lifecycle": "active", "created_at": "2026-01-01T00:00:00Z"},
                 {"id": "a-2", "line": "", "lifecycle": "active", "created_at": "2026-09-01T00:00:00Z"}]
        ai = models.parse_pages("anthropic", [{"data": items}])
        self.assertEqual([i.family for i in ai], [None, None])
        self.assertFalse(any("più recente" in l for l in run("anthropic", {"a-1"}, ai)))

    def test_gemini_latest_no_newer(self):
        gi = self.gem("gemini-flash-latest", "gemini-3.6-flash", "gemini-2.5-flash-latest")
        lines = run("gemini", {"gemini-flash-latest", "gemini-2.5-flash-latest"}, gi)
        self.assertFalse(any("più recente" in l for l in lines), lines)

    def test_gemini_retirement_not_checked_line(self):
        gi = self.gem("gemini-3.6-flash", "gemini-3.6-pro")
        lines = run("gemini", {"gemini-3.6-flash", "gemini-3.6-pro"}, gi)
        self.assertEqual(lines, [f"modelli: gemini: ritiro non controllato: l'elenco non lo dà — {PAGE}"])


class OtherProvidersTest(unittest.TestCase):
    def test_openai_shutdown_and_not_checked(self):
        oi = models.parse_pages("openai", [{"data": [{"id": "gpt-x", "shutdown_date": "2027-02-03"},
                                                    {"id": "gpt-y", "shutdown_date": None}]}])
        lines = run("openai", {"gpt-x", "gpt-y"}, oi)
        self.assertEqual(lines, ["modelli: openai: gpt-x (src/ai.py): ritiro il 2027-02-03 — " + PAGE,
                                 "modelli: openai: più nuovo non controllato: l'elenco non lo dà — " + PAGE])

    def test_openrouter_expiration_and_not_checked(self):
        oi = models.parse_pages("openrouter", [{"data": [{"id": "a/b", "expiration_date": "2027-02-03"},
                                                        {"id": "a/c", "expiration_date": None}]}])
        lines = run("openrouter", {"a/b", "a/c"}, oi)
        self.assertEqual(len(lines), 2, lines)
        self.assertIn("a/b (src/ai.py): ritiro il 2027-02-03", lines[0])
        self.assertIn("più nuovo non controllato: l'elenco non lo dà", lines[1])
        self.assertIn("fornitore originale", lines[1])
        self.assertTrue(lines[1].endswith(" — " + PAGE))

    def test_no_lines_for_provider_without_models_in_use(self):
        oi = [info("openai", "gpt-x")]
        self.assertEqual(run("openai", {"claude-x-5", "altro"}, oi), [])


LINE_FORMS = [
    re.compile(r"modelli: (anthropic|gemini|openai|openrouter): \S+ \(\S+\): "
               r"(esiste \S+, più recente della stessa famiglia|deprecato, ritiro previsto il \S+"
               r"|ritiro il \S+|alias di \S+|non è nell'elenco: ritirato o scritto male) — \S+"),
    re.compile(r"modelli: (anthropic|gemini|openai|openrouter): "
               r"(ritiro|più nuovo) non controllato: l'elenco non lo dà.* — \S+"),
]


class LineFormsTest(unittest.TestCase):
    def all_lines(self):
        ai = [a_info("a-old", created="2026-01-01"), a_info("a-new", created="2026-09-01"),
              a_info("claude-x-4-5-20250101", lifecycle="deprecated", retires="2026-12-31")]
        gi = models.parse_pages("gemini", [{"models": [{"name": "models/gemini-3.5-flash"},
                                                       {"name": "models/gemini-3.6-flash"}]}])
        oi = models.parse_pages("openai", [{"data": [{"id": "gpt-x", "shutdown_date": "2027-02-03"}]}])
        ri = models.parse_pages("openrouter", [{"data": [{"id": "a/b", "expiration_date": None}]}])
        out = []
        out += run("anthropic", {"a-old", "claude-x-4-5", "claude-x-9"}, ai)
        out += run("gemini", {"gemini-3.5-flash", "gemini-9.9-flash"}, gi)
        out += run("openai", {"gpt-x"}, oi)
        out += run("openrouter", {"a/b"}, ri)
        return out

    def test_line_forms(self):
        lines = self.all_lines()
        self.assertGreaterEqual(len(lines), 8)
        for line in lines:
            with self.subTest(line=line):
                self.assertTrue(any(f.fullmatch(line) for f in LINE_FORMS), line)

    def test_control_characters_are_neutralized(self):
        evil = "claude-x-6\x1b[31m\nfalso"
        ai = [a_info("a-old", created="2026-01-01"), a_info(evil, created="2026-09-01")]
        lines = run("anthropic", {"a-old"}, ai, where={"a-old": "src/a\nb\x07.py"})
        self.assertEqual(len(lines), 1)
        for ch in "\x1b\n\x07":
            self.assertNotIn(ch, lines[0])
        self.assertIn("claude-x-6?[31m?falso", lines[0])
        self.assertIn("src/a?b?.py", lines[0])
        unknown = run("anthropic", {"claude-x-5"}, [], where={"claude-x-5": "x\ny"})
        self.assertNotIn("\n", unknown[0])

    def test_lines_ordered_model_first(self):
        gi = models.parse_pages("gemini", [{"models": [{"name": "models/gemini-3.5-flash"},
                                                       {"name": "models/gemini-3.6-flash"}]}])
        lines = run("gemini", {"gemini-3.5-flash", "gemini-9.9-flash"}, gi)
        self.assertEqual(len(lines), 3, lines)
        self.assertIn("(src/ai.py)", lines[0])
        self.assertIn("(src/ai.py)", lines[1])
        self.assertIn("non controllato", lines[2])

    def test_missing_where_entry_is_tolerated(self):
        ai = [a_info("a-old", created="2026-01-01"), a_info("a-new", created="2026-09-01")]
        lines = models.findings("anthropic", models.used({"a-old"}, ai), ai, {"a-old"},
                                where={}, page=PAGE)
        self.assertEqual(len(lines), 1)


class ProvidersTest(unittest.TestCase):
    def test_providers_constant(self):
        self.assertEqual(models.PROVIDERS, ("anthropic", "gemini", "openai", "openrouter"))

    def test_model_info_is_frozen(self):
        with self.assertRaises(dataclasses.FrozenInstanceError):
            info("openai", "gpt-x").id = "altro"


if __name__ == "__main__":
    unittest.main()
