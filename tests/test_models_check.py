import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest import mock

from tests.helpers import BIN, ROOT, TempState, git as g, make_origin_repo, no_network
from tollgate_analysis import models
from tollgate_analysis.models import ModelsFormatError
from tollgate_core import config, git
from tollgate_flow import models_check, modelsfetch
from tollgate_flow.modelsfetch import FetchError

KEY = "sk-PROVA-123"
T0 = datetime(2026, 11, 4, 10, 0, 0, tzinfo=timezone.utc)
FILE = "src/ai/models.py"
PAGE = {name: f"https://docs.{name}.invalid/deprecations"
        for name in ("anthropic", "gemini", "openai", "openrouter")}
MIN = 'schema_version = 1\n[gate]\nmode = "detect"\n'
DEDICATED = ("TOLLGATE_MODELS_ANTHROPIC_KEY, TOLLGATE_MODELS_GEMINI_KEY, "
             "TOLLGATE_MODELS_OPENAI_KEY, TOLLGATE_MODELS_OPENROUTER_KEY")


HINTS = {"anthropic": "claude-(?:[a-z0-9]+-)?[0-9][a-z0-9.-]*", "gemini": "gemini-[0-9][a-z0-9.-]*",
         "openai": "gpt-[a-z0-9][a-z0-9.-]*", "openrouter": ""}
ENV = {"anthropic": ["TOLLGATE_MODELS_ANTHROPIC_KEY", "ANTHROPIC_API_KEY"],
       "gemini": ["TOLLGATE_MODELS_GEMINI_KEY", "GOOGLE_API_KEY", "GEMINI_API_KEY"],
       "openai": ["TOLLGATE_MODELS_OPENAI_KEY", "OPENAI_API_KEY"],
       "openrouter": ["TOLLGATE_MODELS_OPENROUTER_KEY", "OPENROUTER_API_KEY"]}
AUTH = {"gemini": "x-goog-api-key"}
PAGING = {"anthropic": "anthropic", "gemini": "gemini"}


def providers_toml() -> str:
    """File dei fornitori finto, scritto per intero qui: host `.invalid`, nessun dato del vero."""
    out = []
    for name in HINTS:
        out += [f"[{name}]", f'url = "https://{name}.invalid/v1/models"',
                f'paging = "{PAGING.get(name, "none")}"', f'auth = "{AUTH.get(name, "bearer")}"',
                f"env = {json.dumps(ENV[name])}", f'page = "{PAGE[name]}"']
        if HINTS[name]:
            out.append(f"hint = {json.dumps(HINTS[name])}")
        out.append("")
    return "\n".join(out)


def a_model(id, line="sonnet", created="2026-01-01T00:00:00Z", lifecycle="active", retires=None):
    return {"id": id, "line": line, "lifecycle": lifecycle, "created_at": created,
            "retires_at": retires}


def a_page(*items):
    return [{"data": list(items), "has_more": False}]


def g_page(*names):
    return [{"models": [{"name": f"models/{n}"} for n in names]}]


class FakeFetch:
    """`fetch(provider, key, *, deadline)` finto: una risposta (o un'eccezione) per fornitore."""

    def __init__(self, **by_provider):
        self.by_provider = by_provider
        self.calls = []

    def __call__(self, provider, key, *, deadline):
        self.calls.append((provider.name, key, provider.host))
        answer = self.by_provider[provider.name]
        if isinstance(answer, BaseException):
            raise answer
        return answer

    @property
    def names(self):
        return [c[0] for c in self.calls]


class FakeClock:
    def __init__(self):
        self.t = 0.0

    def __call__(self):
        return self.t


class CheckCase(unittest.TestCase):
    def setUp(self):
        self.enterContext(no_network())
        self.tmp = Path(tempfile.mkdtemp(prefix="tollgate-mcheck-"))
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.ts = TempState()
        self.addCleanup(self.ts.cleanup)
        self.plugin = self.tmp / "plugin"
        (self.plugin / "templates").mkdir(parents=True)
        (self.plugin / "templates" / "models.toml").write_text(providers_toml())

    def repo(self, files, toml=MIN):
        self.main, self.origin, _ = make_origin_repo(self.tmp / "r", files, toml)
        return self.main

    def cfg(self, files=(FILE,), extra=""):
        listed = ", ".join(json.dumps(f) for f in files)
        return config.load_config_text(MIN + f"[models]\nfiles = [{listed}]\n" + extra)

    def check(self, cfg, fetch, *, env=None, repo=None, **kw):
        kw.setdefault("now", T0)
        kw.setdefault("plugin_root", self.plugin)
        return models_check.check(self.ts.state, repo or self.main, "origin/main", cfg,
                                  environ=env if env is not None else {"ANTHROPIC_API_KEY": KEY},
                                  fetch=fetch, **kw)

    def cache_file(self, name="anthropic"):
        return self.ts.state.root / "models" / f"{name}.json"


class ComponentAndFilesTest(CheckCase):
    def test_component_off_no_network(self):
        self.repo({FILE: 'm = "claude-old-4-20250101"\n'})
        fetch = FakeFetch()
        cfg = self.cfg(extra="[components]\nmodels_check = false\n")
        with mock.patch.object(git, "object_info_at", side_effect=AssertionError("letto")):
            self.assertEqual(self.check(cfg, fetch), [])
        self.assertEqual(fetch.calls, [])

    def test_no_files_no_network(self):
        self.repo({})
        fetch = FakeFetch()
        empty_root = self.tmp / "senza-templates"
        empty_root.mkdir()
        self.assertEqual(self.check(config.load_config_text(MIN), fetch, plugin_root=empty_root), [])
        self.assertEqual(fetch.calls, [])

    def test_no_files_with_ai_profile_reminds(self):
        self.repo({})
        fetch = FakeFetch()
        cfg = config.load_config_text(MIN + "[profiles.ai]\nkind = \"cross\"\n")
        self.assertEqual(self.check(cfg, fetch), [
            "modelli: il profilo ai è dichiarato ma [models] files è vuoto: "
            "la sentinella non sa dove cercare"])
        off = config.load_config_text(MIN + "[profiles.ai]\nkind = \"cross\"\n"
                                      "[components]\nmodels_check = false\n")
        self.assertEqual(self.check(off, fetch), [])
        self.assertEqual(fetch.calls, [])

    def test_providers_file_missing_gives_single_line(self):
        self.repo({FILE: 'm = "claude-old-4-20250101"\n'})
        bare = self.tmp / "bare"
        bare.mkdir()
        self.assertEqual(self.check(self.cfg(), FakeFetch(), plugin_root=bare),
                         ["modelli: controllo non riuscito (ProvidersError)"])

    def test_reads_files_from_ref_not_worktree(self):
        repo = self.repo({FILE: 'm = "claude-old-4-20250101"\n'})
        (repo / FILE).write_text('m = "claude-other-4-20250101"\n')
        (repo / "src" / "ai" / "locale.py").write_text('m = "claude-old-4-20250101"\n')
        fetch = FakeFetch(anthropic=a_page(
            a_model("claude-old-4-20250101", retires="2026-12-31T00:00:00Z", lifecycle="deprecated"),
            a_model("claude-other-4-20250101", lifecycle="deprecated",
                    retires="2027-01-01T00:00:00Z")))
        lines = self.check(self.cfg([FILE, "src/ai/locale.py"]), fetch)
        self.assertIn(f"modelli: anthropic: claude-old-4-20250101 ({FILE}): deprecato, ritiro "
                      f"previsto il 2026-12-31 — {PAGE['anthropic']}", lines)
        self.assertFalse(any("claude-other-4" in line for line in lines))
        self.assertIn("modelli: src/ai/locale.py: non trovato su origin/main", lines)

    def test_missing_file_line(self):
        self.repo({"altro.py": "x = 1\n"})
        fetch = FakeFetch()
        self.assertEqual(self.check(self.cfg(), fetch),
                         [f"modelli: {FILE}: non trovato su origin/main"])
        self.assertEqual(fetch.calls, [])

    def test_binary_or_large_file_line(self):
        self.repo({"b.bin": "ab\0cd", "big.py": 'm = "claude-old-4-20250101"\n' + "x" * 300_000,
                   FILE: "x = 1\n"})
        real_show = git.show
        with mock.patch.object(git, "show", wraps=real_show) as show:
            lines = self.check(self.cfg(["b.bin", "big.py", FILE]), FakeFetch())
        self.assertEqual(lines, ["modelli: b.bin: non letto (binario o oltre 256 KiB)",
                                 "modelli: big.py: non letto (binario o oltre 256 KiB)"])
        self.assertEqual([c.args[2] for c in show.call_args_list], ["b.bin", FILE])

    def test_folder_entry_line(self):
        self.repo({FILE: "x = 1\n"})
        self.assertEqual(self.check(self.cfg(["src/ai"]), FakeFetch()),
                         ["modelli: src/ai: non è un file"])

    def test_file_names_are_neutralized(self):
        self.repo({})
        cfg = self.cfg()
        cfg.data["models"]["files"] = ["a\x1b[31m.py"]
        lines = self.check(cfg, FakeFetch())
        self.assertEqual(lines, ["modelli: a?[31m.py: non trovato su origin/main"])

    def test_no_literals_no_network(self):
        self.repo({FILE: "x = 1\nname = 'due parole'\n"})
        fetch = FakeFetch()
        self.assertEqual(self.check(self.cfg(), fetch), [])
        self.assertEqual(fetch.calls, [])


class KeysTest(CheckCase):
    def test_no_key_at_all_one_line_no_network(self):
        self.repo({FILE: 'm = "claude-old-4-20250101"\n'})
        fetch = FakeFetch()
        for env in ({}, {"ANTHROPIC_API_KEY": "", "GOOGLE_API_KEY": "  "}):
            self.assertEqual(self.check(self.cfg(), fetch, env=env),
                             [f"modelli: nessuna chiave nell'ambiente: imposta {DEDICATED}"])
        self.assertEqual(fetch.calls, [])

    def test_some_keys_missing_lines(self):
        self.repo({FILE: 'a = "gemini-3.6-flash"\nb = "claude-x-5"\n'})
        fetch = FakeFetch(anthropic=a_page(a_model("claude-old-4-20250101")))
        lines = self.check(self.cfg(), fetch)
        self.assertIn("modelli: gemini: non controllato: manca la chiave "
                      "(TOLLGATE_MODELS_GEMINI_KEY, GOOGLE_API_KEY, GEMINI_API_KEY)", lines)
        self.assertIn(f"modelli: anthropic: claude-x-5 ({FILE}): "
                      f"non è nell'elenco: ritirato o scritto male — {PAGE['anthropic']}", lines)
        self.assertEqual(len(lines), 2)
        self.assertFalse(any(l.startswith(("modelli: openai", "modelli: openrouter"))
                             for l in lines))
        self.assertEqual(fetch.names, ["anthropic"])

    def test_dedicated_variable_wins_and_key_is_passed_to_fetch_only(self):
        self.repo({FILE: 'm = "claude-old-4-20250101"\n'})
        fetch = FakeFetch(anthropic=a_page(a_model("claude-old-4-20250101")))
        env = {"TOLLGATE_MODELS_ANTHROPIC_KEY": "sk-DEDICATA-1", "ANTHROPIC_API_KEY": KEY}
        lines = self.check(self.cfg(), fetch, env=env)
        self.assertEqual([c[1] for c in fetch.calls], ["sk-DEDICATA-1"])
        self.assertFalse(any("sk-" in line for line in lines))
        self.assertNotIn("sk-", self.cache_file().read_text())


class ProvidersTest(CheckCase):
    def test_one_provider_fails_other_reports(self):
        self.repo({FILE: 'a = "claude-old-4-20250101"\nb = "gemini-3.6-flash"\n'})
        fetch = FakeFetch(anthropic=FetchError("chiave rifiutata"),
                          gemini=g_page("gemini-3.6-flash", "gemini-3.7-flash"))
        lines = self.check(self.cfg(), fetch,
                           env={"ANTHROPIC_API_KEY": KEY, "GEMINI_API_KEY": KEY + "-g"})
        self.assertEqual(lines, [
            f"modelli: gemini: gemini-3.6-flash ({FILE}): esiste gemini-3.7-flash, più recente "
            f"della stessa famiglia — {PAGE['gemini']}",
            "modelli: anthropic: elenco non letto: chiave rifiutata",
            f"modelli: gemini: ritiro non controllato: l'elenco non lo dà — {PAGE['gemini']}"])
        self.assertFalse(any(KEY in line for line in lines))

    def test_corrupt_cache_refetched(self):
        self.repo({FILE: 'm = "claude-old-4-20250101"\n'})
        self.cache_file().parent.mkdir(parents=True)
        self.cache_file().write_text("{ non json")
        fetch = FakeFetch(anthropic=a_page(a_model("claude-old-4-20250101")))
        self.assertEqual(self.check(self.cfg(), fetch), [])
        self.assertEqual(fetch.names, ["anthropic"])
        self.assertIn("pages", json.loads(self.cache_file().read_text()))

    def test_deadline_skips_remaining_providers(self):
        self.repo({FILE: 'a = "claude-old-4-20250101"\nb = "gemini-3.6-flash"\nc = "gpt-5"\n'})
        clock = FakeClock()

        class Slow(FakeFetch):
            def __call__(self, provider, key, *, deadline):
                clock.t += 100
                return super().__call__(provider, key, deadline=deadline)

        fetch = Slow(anthropic=a_page(a_model("claude-old-4-20250101")))
        lines = self.check(self.cfg(), fetch, clock=clock,
                           env={"ANTHROPIC_API_KEY": KEY, "GOOGLE_API_KEY": KEY,
                                "OPENAI_API_KEY": KEY})
        self.assertEqual(lines, ["modelli: gemini: saltato, tempo del controllo finito",
                                 "modelli: openai: saltato, tempo del controllo finito"])
        self.assertEqual(fetch.names, ["anthropic"])

    def test_gemini_provider_line_comes_after_model_lines_of_all_providers(self):
        self.repo({FILE: 'a = "claude-old-4-20250101"\nb = "gemini-3.6-flash"\n'})
        fetch = FakeFetch(
            anthropic=a_page(a_model("claude-old-4-20250101", lifecycle="deprecated"),),
            gemini=g_page("gemini-3.6-flash"))
        lines = self.check(self.cfg(), fetch,
                           env={"ANTHROPIC_API_KEY": KEY, "GOOGLE_API_KEY": KEY})
        self.assertEqual(lines, [
            f"modelli: anthropic: claude-old-4-20250101 ({FILE}): deprecato, ritiro previsto il "
            f"data non indicata — {PAGE['anthropic']}",
            f"modelli: gemini: ritiro non controllato: l'elenco non lo dà — {PAGE['gemini']}"])

    def test_lines_capped(self):
        names = [f"claude-d{n:02d}-4-20250101" for n in range(20)]
        self.repo({FILE: "".join(f'm{i} = "{n}"\n' for i, n in enumerate(names))})
        fetch = FakeFetch(anthropic=a_page(*[
            a_model(n, lifecycle="deprecated", retires="2026-12-31T00:00:00Z") for n in names]))
        lines = self.check(self.cfg(), fetch)
        self.assertEqual(len(lines), 13)
        self.assertEqual(lines[:12], [
            f"modelli: anthropic: {n} ({FILE}): deprecato, ritiro previsto il 2026-12-31 — "
            f"{PAGE['anthropic']}" for n in names[:12]])
        self.assertEqual(lines[12], "modelli: … e altri 8 avvisi")

    def test_end_to_end_anthropic_newer_and_deprecated(self):
        self.repo({FILE: 'a = "claude-old-4-20250101"\nb = "claude-dep-4-20250201"\n'
                         'c = "claude-code"\n'})
        fetch = FakeFetch(anthropic=a_page(
            a_model("claude-old-4-20250101", created="2025-01-01T00:00:00Z"),
            a_model("claude-new-5-20260301", created="2026-03-01T00:00:00Z"),
            a_model("claude-dep-4-20250201", line="haiku", lifecycle="deprecated",
                    retires="2026-12-31T00:00:00Z", created="2025-02-01T00:00:00Z")))
        self.assertEqual(self.check(self.cfg(), fetch), [
            f"modelli: anthropic: claude-dep-4-20250201 ({FILE}): deprecato, ritiro previsto il "
            f"2026-12-31 — {PAGE['anthropic']}",
            f"modelli: anthropic: claude-old-4-20250101 ({FILE}): esiste claude-new-5-20260301, "
            f"più recente della stessa famiglia — {PAGE['anthropic']}"])

    def test_plugin_root_resolved_at_call(self):
        self.repo({FILE: 'm = "claude-old-4-20250101"\n'})
        fetch = FakeFetch(anthropic=a_page(a_model("claude-old-4-20250101")))
        with mock.patch.object(models_check, "PLUGIN_ROOT", self.plugin):
            models_check.check(self.ts.state, self.main, "origin/main", self.cfg(),
                               environ={"ANTHROPIC_API_KEY": KEY}, now=T0, fetch=fetch)
        self.assertEqual(fetch.calls[0][2], "anthropic.invalid")

    def test_provider_line_recognised_for_openai_and_openrouter(self):
        self.repo({FILE: 'a = "gpt-5-old"\nb = "openai/gpt-5-old"\nc = "anthropic/claude-x-5"\n'})
        fetch = FakeFetch(
            openai=[{"data": [{"id": "gpt-5-old", "shutdown_date": "2027-02-03"}]}],
            openrouter=[{"data": [{"id": "openai/gpt-5-old", "expiration_date": "2027-03-04"}]}])
        lines = self.check(self.cfg(), fetch, env={"OPENAI_API_KEY": KEY,
                                                    "OPENROUTER_API_KEY": KEY})
        self.assertEqual(lines, [
            f"modelli: openai: gpt-5-old ({FILE}): ritiro il 2027-02-03 — {PAGE['openai']}",
            f"modelli: openrouter: openai/gpt-5-old ({FILE}): ritiro il 2027-03-04 — "
            f"{PAGE['openrouter']}",
            f"modelli: openai: più nuovo non controllato: l'elenco non lo dà — {PAGE['openai']}",
            f"modelli: openrouter: più nuovo non controllato: l'elenco non lo dà, guarda la pagina "
            f"del fornitore originale — {PAGE['openrouter']}"])

    def test_importing_models_check_does_not_load_the_net_client(self):
        code = ("import sys\n"
                f"sys.path.insert(0, {str(BIN)!r})\n"
                "import tollgate_flow.models_check\n"
                "print('tollgate_flow.modelsfetch' in sys.modules)\n")
        r = subprocess.run([sys.executable, "-B", "-c", code], capture_output=True, text=True,
                           timeout=60, cwd=tempfile.gettempdir())
        self.assertEqual((r.returncode, r.stdout.strip()), (0, "False"), r.stderr)

    def test_real_plugin_root_is_the_default(self):
        self.assertEqual(models_check.PLUGIN_ROOT, ROOT)
        self.assertEqual((models_check.MAX_LINES, models_check.DEADLINE_S,
                          models_check.MAX_FILE_BYTES), (12, 20, 256 * 1024))


class CacheLinesTest(CheckCase):
    def setUp(self):
        super().setUp()
        self.repo({FILE: 'm = "claude-old-4-20250101"\n'})
        self.fetch = FakeFetch(anthropic=a_page(a_model("claude-old-4-20250101")))

    def test_fresh_cache_line_hidden_when_asked(self):
        self.assertEqual(self.check(self.cfg(), self.fetch), [])
        self.assertEqual(self.check(self.cfg(), self.fetch),
                         ["modelli: anthropic: elenco dalla cache del 2026-11-04"])
        self.assertEqual(self.check(self.cfg(), self.fetch, show_cache=False), [])
        self.assertEqual(len(self.fetch.calls), 1)
        self.fetch.by_provider["anthropic"] = FetchError("tempo scaduto")
        self.assertEqual(
            self.check(self.cfg(), self.fetch, show_cache=False, refresh=True),
            ["modelli: anthropic: rete non riuscita (tempo scaduto), "
             "elenco dalla cache del 2026-11-04"])


class NeverRaisesTest(CheckCase):
    def setUp(self):
        super().setUp()
        self.repo({FILE: 'm = "claude-old-4-20250101"\n'})
        self.fetch = FakeFetch(anthropic=a_page(a_model("claude-old-4-20250101")))

    def test_check_never_raises(self):
        failed = "modelli: controllo non riuscito (RuntimeError)"
        self.assertEqual(self.check(self.cfg(), FakeFetch(anthropic=RuntimeError("boom"))),
                         [failed])
        with mock.patch.object(git, "object_info_at", side_effect=RuntimeError("boom")):
            self.assertEqual(self.check(self.cfg(), self.fetch), [failed])
        with mock.patch.object(git, "show", side_effect=RuntimeError("boom")):
            self.assertEqual(self.check(self.cfg(), self.fetch), [failed])
        with mock.patch.object(models, "findings", side_effect=RuntimeError("boom")):
            self.assertEqual(self.check(self.cfg(), self.fetch), [failed])

    def test_unexpected_page_shape_is_one_line_for_that_provider(self):
        with mock.patch.object(models, "parse_pages", side_effect=ModelsFormatError("x")):
            self.assertEqual(self.check(self.cfg(), self.fetch),
                             ["modelli: anthropic: elenco non letto: forma inattesa"])
        self.assertFalse(self.cache_file().exists())

    def test_error_text_never_carries_the_key(self):
        err = FetchError("errore HTTP 500")
        lines = self.check(self.cfg(), FakeFetch(anthropic=err))
        self.assertEqual(lines, ["modelli: anthropic: elenco non letto: errore HTTP 500"])
        boom = RuntimeError(f"url con {KEY}")
        lines = self.check(self.cfg(), FakeFetch(anthropic=boom))
        self.assertEqual(lines, ["modelli: controllo non riuscito (RuntimeError)"])


if __name__ == "__main__":
    unittest.main()
