import unittest

from tollgate_analysis import research as r

WT = "/w"

NOTE = """## Letto nel progetto
- src/app.py
- `src/util.py` — helper

## Documentazione
- https://docs.python.org/3/library/tomllib.html — parsing TOML
- context7:/python/cpython - la libreria standard

## Cosa ho trovato
tomllib legge solo in binario.
Quindi apro il file con "rb".
"""

URL = "https://docs.python.org/3/library/tomllib.html"
LOOKUPS = [("read", "src/app.py"), ("grep", "src/util.py"), ("fetch", URL),
           ("docs", "/python/cpython")]


def note(**kw):
    base = dict(files=["src/app.py"], sources=[], no_external="non servono fonti esterne",
                findings="trovato", problems=[])
    base.update(kw)
    return r.Note(**base)


class EnforcedTest(unittest.TestCase):
    def test_enforced(self):
        self.assertTrue(r.enforced("---\nname: rules-base\napproved: 2026-11-02\n---\ncorpo\n"))
        self.assertFalse(r.enforced("---\nname: rules-base\napproved:\n---\ncorpo\n"))
        self.assertFalse(r.enforced("---\nname: rules-base\napproved: \"\"\n---\n"))
        self.assertFalse(r.enforced("corpo senza frontmatter\napproved: 2026-11-02\n"))
        self.assertFalse(r.enforced("---\nname: x\n---\napproved: 2026-11-02\n"))
        self.assertFalse(r.enforced(None))
        self.assertFalse(r.enforced(""))

    def test_active(self):
        self.assertTrue(r.active(1, True))
        self.assertFalse(r.active(0, True))
        self.assertFalse(r.active(1, False))
        self.assertFalse(r.active(0, False))


class NormalizeTest(unittest.TestCase):
    def test_url_forms(self):
        want = "https://docs.python.org/3/library/tomllib.html"
        for u in ("HTTPS://Docs.Python.org:443/3/library/tomllib.html#module-tomllib",
                  "https://docs.python.org/3/library/tomllib.html/", want):
            with self.subTest(url=u):
                self.assertEqual(r.normalize_url(u), want)
        self.assertNotEqual(r.normalize_url("https://docs.python.org/3/library/json.html"), want)
        self.assertEqual(r.normalize_url("https://x.org/a?v=2#f"), "https://x.org/a?v=2")
        self.assertEqual(r.normalize_url("https://x.org"), r.normalize_url("https://x.org/"))
        self.assertEqual(r.normalize_url("http://x.org:80/a"), "http://x.org/a")
        self.assertEqual(r.normalize_url("http://x.org:8080/a"), "http://x.org:8080/a")
        for bad in ("ftp://x", "file:///etc/passwd", "https:///path", "", "https://x.org:abc/"):
            with self.subTest(url=bad):
                self.assertIsNone(r.normalize_url(bad))

    def test_normalize_path_forms(self):
        for p in ("app.py", "./app.py", "/w/src/app.py"):
            with self.subTest(path=p):
                self.assertEqual(r.normalize_path(p, cwd="/w/src", worktree=WT), "src/app.py")
        self.assertIsNone(r.normalize_path("../../etc/passwd", cwd="/w/src", worktree=WT))
        self.assertIsNone(r.normalize_path("/main/src/app.py", cwd="/w/src", worktree=WT))
        self.assertIsNone(r.normalize_path("~/x", cwd="/w/src", worktree=WT))
        self.assertIsNone(r.normalize_path("", cwd="/w/src", worktree=WT))
        self.assertIsNone(r.normalize_path("/wx/a.py", cwd="/w", worktree=WT))
        self.assertEqual(r.normalize_path("../a.py", cwd="/w/src", worktree="/w/"), "a.py")


class ParseTest(unittest.TestCase):
    def test_parse_note_complete(self):
        n = r.parse_note(NOTE)
        self.assertEqual(n.problems, [])
        self.assertEqual(n.files, ["src/app.py", "src/util.py"])
        self.assertEqual(n.sources, [
            r.Source(URL, "url", "parsing TOML"),
            r.Source("/python/cpython", "context7", "la libreria standard")])
        self.assertIsNone(n.no_external)
        self.assertEqual(n.findings,
                         'tomllib legge solo in binario.\nQuindi apro il file con "rb".')

    def test_parse_note_separators(self):
        n = r.parse_note("## Letto nel progetto\n- a.py\n## Documentazione\n"
                         "- https://x.org/a — uno\n- https://x.org/b - due\n"
                         "## Cosa ho trovato\nok\n")
        self.assertEqual(n.problems, [])
        self.assertEqual([s.text for s in n.sources], ["uno", "due"])

    def test_parse_note_missing_sections(self):
        n = r.parse_note("## Documentazione\n- https://x.org/a — uno\n## Cosa ho trovato\nok\n")
        self.assertEqual(len(n.problems), 1)
        self.assertIn(r.SECTION_FILES, n.problems[0])
        n = r.parse_note("## Letto nel progetto\n- a.py\n## Nessuna fonte esterna\nmotivo\n")
        self.assertEqual(len(n.problems), 1)
        self.assertIn(r.SECTION_FOUND, n.problems[0])
        n = r.parse_note("## Letto nel progetto\n- a.py\n## Cosa ho trovato\nok\n")
        self.assertEqual(len(n.problems), 1)
        self.assertIn(r.SECTION_DOCS, n.problems[0])
        self.assertIn(r.SECTION_NONE, n.problems[0])

    def test_parse_note_empty_sections(self):
        n = r.parse_note("## Letto nel progetto\n\n## Nessuna fonte esterna\nm\n"
                         "## Cosa ho trovato\n\n")
        self.assertEqual(len(n.problems), 2)

    def test_parse_note_unknown_source(self):
        n = r.parse_note("## Letto nel progetto\n- a.py\n## Documentazione\n- ftp://x/a — boh\n"
                         "## Cosa ho trovato\nok\n")
        self.assertEqual(len(n.problems), 1)
        self.assertIn("ftp://x/a", n.problems[0])

    def test_parse_note_both_sources_and_none(self):
        n = r.parse_note(NOTE + "\n## Nessuna fonte esterna\nnon serve\n")
        self.assertEqual(len(n.problems), 1)
        self.assertIn(r.SECTION_NONE, n.problems[0])
        self.assertIn(r.SECTION_DOCS, n.problems[0])

    def test_parse_note_none_with_reason(self):
        n = r.parse_note("## Letto nel progetto\n- a.py\n## Nessuna fonte esterna\n"
                         "solo codice del progetto\n## Cosa ho trovato\nok\n")
        self.assertEqual(n.problems, [])
        self.assertEqual(n.no_external, "solo codice del progetto")
        self.assertEqual(n.sources, [])

    def test_parse_note_too_long(self):
        n = r.parse_note(NOTE + "x" * 8000)
        self.assertIn("nota oltre 8000 caratteri", n.problems)

    def test_parse_note_never_raises(self):
        for text in ("", "\x00", "## ", "##Letto nel progetto", "- x"):
            with self.subTest(text=text):
                self.assertTrue(r.parse_note(text).problems)


class CheckTest(unittest.TestCase):
    def test_check_note_valid(self):
        self.assertEqual(r.check_note(r.parse_note(NOTE), LOOKUPS, worktree=WT), [])

    def test_check_note_source_not_read(self):
        out = r.check_note(r.parse_note(NOTE), [l for l in LOOKUPS if l[0] != "fetch"],
                           worktree=WT)
        self.assertEqual(len(out), 1)
        self.assertIn(URL, out[0])

    def test_check_note_url_normalized(self):
        n = r.parse_note(NOTE.replace(URL, "HTTPS://Docs.Python.org/3/library/tomllib.html#x"))
        self.assertEqual(r.check_note(n, LOOKUPS, worktree=WT), [])

    def test_check_note_file_not_read(self):
        out = r.check_note(r.parse_note(NOTE), [l for l in LOOKUPS if l[1] != "src/util.py"],
                           worktree=WT)
        self.assertEqual(len(out), 1)
        self.assertIn("src/util.py", out[0])

    def test_check_note_file_forms(self):
        for kind in ("read", "grep", "bash_read"):
            with self.subTest(kind=kind):
                self.assertEqual(r.check_note(note(), [(kind, "src/app.py")], worktree=WT), [])
        self.assertEqual(r.check_note(note(files=["./src/../src/app.py"]),
                                      [("read", "src/app.py")], worktree=WT), [])
        out = r.check_note(note(files=["../out.py"]), [("read", "out.py")], worktree=WT)
        self.assertEqual(len(out), 1)
        self.assertIn("../out.py", out[0])

    def test_check_note_glob_does_not_count(self):
        out = r.check_note(note(), [("search", "src/app.py"), ("glob", "src/app.py"),
                                    ("fetch", "src/app.py")], worktree=WT)
        self.assertEqual(len(out), 1)
        self.assertIn("src/app.py", out[0])

    def test_check_note_no_external_without_reason(self):
        out = r.check_note(note(no_external=""), [("read", "src/app.py")], worktree=WT)
        self.assertEqual(len(out), 1)
        self.assertIn(r.SECTION_NONE, out[0])
        self.assertEqual(r.check_note(note(), [("read", "src/app.py")], worktree=WT), [])

    def test_check_note_context7(self):
        n = note(no_external=None, sources=[r.Source("/python/cpython", "context7", "x")])
        self.assertEqual(r.check_note(n, [("read", "src/app.py"), ("docs", "/python/cpython")],
                                      worktree=WT), [])
        out = r.check_note(n, [("read", "src/app.py"), ("fetch", "/python/cpython")], worktree=WT)
        self.assertEqual(len(out), 1)
        self.assertIn("/python/cpython", out[0])

    def test_search_alone_not_a_source(self):
        n = note(no_external=None, sources=[r.Source(URL, "url", "x")])
        out = r.check_note(n, [("read", "src/app.py"), ("search", "tomllib")], worktree=WT)
        self.assertEqual(len(out), 1)
        self.assertIn(URL, out[0])

    def test_check_note_collects_all_problems(self):
        n = r.parse_note(NOTE)
        out = r.check_note(n, [], worktree=WT)
        self.assertEqual(len(out), 4)

    def test_check_note_includes_parse_problems(self):
        n = r.parse_note("")
        self.assertEqual(r.check_note(n, [], worktree=WT), n.problems)

    def test_check_note_bad_url_source(self):
        n = note(no_external=None, sources=[r.Source("ftp://x", "url", "x")])
        out = r.check_note(n, [("read", "src/app.py")], worktree=WT)
        self.assertEqual(len(out), 1)
        self.assertIn("ftp://x", out[0])


class DocToolsTest(unittest.TestCase):
    def test_doc_tools(self):
        for name in ("mcp__context7__resolve-library-id", "mcp__context7__query-docs",
                     "mcp__plugin_context7_context7__query-docs",
                     "mcp__plugin_context7_context7__get-library-docs"):
            with self.subTest(name=name):
                self.assertTrue(r.is_doc_tool(name))
        for name in ("mcp__github__create_issue", "mcp__plugin_context7_context7__authenticate",
                     "Read", ""):
            with self.subTest(name=name):
                self.assertFalse(r.is_doc_tool(name))

    def test_doc_library(self):
        self.assertEqual(r.doc_library({"libraryId": "/python/cpython", "query": "x"}),
                         "/python/cpython")
        self.assertEqual(r.doc_library({"context7CompatibleLibraryID": "/a/b"}), "/a/b")
        self.assertEqual(r.doc_library({"libraryId": "/x/y", "context7CompatibleLibraryID": "/a/b"}),
                         "/x/y")
        for bad in ({}, {"libraryId": ""}, {"libraryId": 3}, {"libraryName": "react"}):
            with self.subTest(bad=bad):
                self.assertIsNone(r.doc_library(bad))

    def test_attribute_unnamed_tools_empty(self):
        self.assertEqual(r.ATTRIBUTE_UNNAMED_TOOLS, frozenset())


class SubmitCommandTest(unittest.TestCase):
    def test_submit_command_quotes_delimiter(self):
        cmd = r.submit_command('python3 "/p/bin/tollgate"', 3)
        lines = cmd.split("\n")
        self.assertEqual(lines[0], "python3 \"/p/bin/tollgate\" research submit 3 "
                                   "<<'NOTA_DI_RICERCA_FINE'")
        self.assertEqual(lines[-1], r.HEREDOC_END)
        self.assertNotIn("TOLLGATE_", cmd)
        for s in (r.SECTION_FILES, r.SECTION_DOCS, r.SECTION_NONE, r.SECTION_FOUND):
            self.assertIn("## " + s, cmd)

    def test_template_is_parsed_with_problems(self):
        body = r.submit_command("p", 1).split("\n", 1)[1].rsplit("\n", 1)[0]
        self.assertTrue(r.parse_note(body).problems)


if __name__ == "__main__":
    unittest.main()
