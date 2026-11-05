import io
import json
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import unittest
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest import mock
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, urlsplit

from tests import helpers
from tests.helpers import BIN, ROOT, TempState, no_network
from tests.test_layers import imported_modules
from tollgate_analysis.models import ModelsFormatError, PROVIDERS
from tollgate_core import clock
from tollgate_flow import modelsfetch
from tollgate_flow.modelsfetch import (Deadline, DeadlineSkipped, FetchError, Provider, ProvidersError, api_key,
                                       build_opener, cached_pages, fetch_pages, load_providers)

KEY = "sk-PROVA-123"
T0 = datetime(2026, 11, 4, 10, 0, 0, tzinfo=timezone.utc)

VALID_TOML = """\
[anthropic]
url = "https://anthropic.invalid/v1/models?limit=1000"
paging = "anthropic"
auth = "bearer"
headers = { anthropic-version = "2026-10-21" }
env = ["TOLLGATE_MODELS_ANTHROPIC_KEY", "ANTHROPIC_API_KEY"]
page = "https://docs.anthropic.invalid/deprecations"
hint = "claude-[0-9]+"

[gemini]
url = "https://gemini.invalid/v1beta/models?pageSize=1000"
paging = "gemini"
auth = "x-goog-api-key"
env = ["TOLLGATE_MODELS_GEMINI_KEY", "GOOGLE_API_KEY", "GEMINI_API_KEY"]
page = "https://docs.gemini.invalid/deprecations"
hint = "gemini-[0-9]+"

[openai]
url = "https://openai.invalid/v1/models"
paging = "none"
auth = "bearer"
env = ["TOLLGATE_MODELS_OPENAI_KEY", "OPENAI_API_KEY"]
page = "https://docs.openai.invalid/deprecations"
hint = "gpt-[0-9]+"

[openrouter]
url = "https://openrouter.invalid/api/v1/models"
paging = "none"
auth = "bearer"
env = ["TOLLGATE_MODELS_OPENROUTER_KEY", "OPENROUTER_API_KEY"]
page = "https://docs.openrouter.invalid/models"
"""


def make_provider(**kw) -> Provider:
    base = dict(name="anthropic", url="https://api.example.invalid/v1/models?limit=1000",
                host="api.example.invalid", paging="none", auth="bearer", headers={}, env=(),
                page="https://docs.example.invalid/x", hint="")
    base.update(kw)
    return Provider(**base)


class FakeResponse:
    def __init__(self, body=None, status=200, raw=None):
        data = raw if raw is not None else json.dumps(body).encode()
        self._buf = io.BytesIO(data)
        self.status = status
        self.headers = {"Content-Type": "application/json"}
        self.closed = False
        self.on_read = None

    def read(self, n=-1):
        chunk = self._buf.read(n)
        if self.on_read:
            self.on_read(chunk)
        return chunk

    def close(self):
        self.closed = True


class EndlessResponse(FakeResponse):
    def __init__(self):
        super().__init__(raw=b"")
        self.total = 0

    def read(self, n=-1):
        self.total += n
        chunk = b"x" * n
        if self.on_read:
            self.on_read(chunk)
        return chunk


class FakeOpener:
    """`open(request, timeout)` registra la richiesta e restituisce o solleva il prossimo."""

    def __init__(self, *outcomes, on_open=None):
        self.outcomes = list(outcomes)
        self.requests = []
        self.timeouts = []
        self.on_open = on_open

    def open(self, request, timeout=None):
        self.requests.append(request)
        self.timeouts.append(timeout)
        if self.on_open:
            self.on_open()
        out = self.outcomes.pop(0)
        if isinstance(out, BaseException):
            raise out
        return out


def headers_of(request) -> dict:
    return {k.lower(): v for k, v in request.header_items()}


def write_root(tmp: Path, text: str) -> Path:
    (tmp / "templates").mkdir(parents=True, exist_ok=True)
    (tmp / "templates" / "models.toml").write_text(text, encoding="utf-8")
    return tmp


class FakeClock:
    def __init__(self):
        self.t = 100.0

    def __call__(self):
        return self.t


class NetCase(unittest.TestCase):
    def setUp(self):
        self.enterContext(no_network())
        self.tmp = Path(tempfile.mkdtemp(prefix="tollgate-test-mf-"))
        self.addCleanup(shutil.rmtree, self.tmp, True)


class ProvidersFileTest(NetCase):
    def load(self, text):
        return load_providers(write_root(self.tmp, text))

    def test_real_providers_file_loads(self):
        providers = load_providers(ROOT)
        self.assertEqual(tuple(sorted(providers)), tuple(sorted(PROVIDERS)))
        for name, p in providers.items():
            with self.subTest(provider=name):
                self.assertEqual(p.name, name)
                self.assertEqual(urlsplit(p.url).scheme, "https")
                self.assertEqual(urlsplit(p.url).hostname, p.host)
                self.assertTrue(p.env)
                self.assertTrue(p.page.startswith("https://"))
        self.assertEqual(providers["gemini"].auth, "x-goog-api-key")
        self.assertEqual(providers["gemini"].paging, "gemini")
        self.assertIn("anthropic-version", providers["anthropic"].headers)
        self.assertEqual(providers["anthropic"].paging, "anthropic")
        self.assertEqual(providers["openai"].paging, "none")
        self.assertIn("limit=1000", providers["anthropic"].url)
        self.assertIn("pageSize=1000", providers["gemini"].url)

    def test_valid_temp_file_loads(self):
        providers = self.load(VALID_TOML)
        self.assertEqual(providers["anthropic"].host, "anthropic.invalid")
        self.assertEqual(providers["anthropic"].headers, {"anthropic-version": "2026-10-21"})
        self.assertEqual(providers["openrouter"].hint, "")
        self.assertEqual(providers["gemini"].env[1], "GOOGLE_API_KEY")

    def test_providers_file_rejects_bad_urls_keys_and_providers(self):
        a = "https://anthropic.invalid/v1/models?limit=1000"
        cases = {
            "http": VALID_TOML.replace(a, a.replace("https", "http")),
            "utente": VALID_TOML.replace("https://anthropic.invalid", "https://u@anthropic.invalid"),
            "password": VALID_TOML.replace("https://anthropic.invalid",
                                           "https://u:p@anthropic.invalid"),
            "porta": VALID_TOML.replace("anthropic.invalid/v1", "anthropic.invalid:8443/v1"),
            "key in query": VALID_TOML.replace("limit=1000", "limit=1000&key=abc"),
            "KEY in query": VALID_TOML.replace("limit=1000", "Key=abc"),
            "chiave sconosciuta": VALID_TOML.replace('auth = "bearer"', 'auth = "bearer"\nfoo = 1',
                                                     1),
            "fornitore in più": VALID_TOML + '\n[extra]\nurl = "https://x.invalid/"\n',
            "fornitore mancante": VALID_TOML[:VALID_TOML.index("[openrouter]")],
            "paging sconosciuto": VALID_TOML.replace('paging = "gemini"', 'paging = "altro"'),
            "env vuoto": VALID_TOML.replace(
                'env = ["TOLLGATE_MODELS_OPENAI_KEY", "OPENAI_API_KEY"]', "env = []"),
            "env non valido": VALID_TOML.replace("OPENAI_API_KEY", "openai key"),
            "hint non valido": VALID_TOML.replace('"gpt-[0-9]+"', '"gpt-("'),
            "intestazione non valida": VALID_TOML.replace(
                'headers = { anthropic-version = "2026-10-21" }',
                'headers = { "bad name" = "x" }'),
            "toml rotto": "[anthropic\n",
            "senza host": VALID_TOML.replace("https://anthropic.invalid/v1/models?limit=1000",
                                             "https:///v1/models"),
        }
        for label, text in cases.items():
            with self.subTest(case=label):
                with self.assertRaises(ProvidersError):
                    self.load(text)

    def test_missing_file_is_providers_error(self):
        with self.assertRaises(ProvidersError):
            load_providers(self.tmp)

    def test_real_hosts_not_in_bin(self):
        hosts = {p.host for p in load_providers(ROOT).values()}
        self.assertEqual(len(hosts), 4)
        for path in (ROOT / "bin").rglob("*"):
            if not path.is_file() or "__pycache__" in path.parts:
                continue
            text = path.read_bytes().decode("utf-8", errors="ignore")
            for host in hosts:
                with self.subTest(file=str(path.relative_to(ROOT)), host=host):
                    self.assertNotIn(host, text)

    def test_model_key_vars_match_providers_file(self):
        union = set()
        for p in load_providers(ROOT).values():
            union |= set(p.env)
        self.assertEqual(set(helpers.MODEL_KEY_VARS), union)


class ApiKeyTest(NetCase):
    def test_api_key_order(self):
        p = make_provider(env=("TOLLGATE_MODELS_X_KEY", "X_API_KEY"))
        self.assertEqual(api_key(p, {"TOLLGATE_MODELS_X_KEY": "ded", "X_API_KEY": "std"}), "ded")
        self.assertEqual(api_key(p, {"X_API_KEY": "std"}), "std")
        self.assertEqual(api_key(p, {"TOLLGATE_MODELS_X_KEY": "", "X_API_KEY": "std"}), "std")
        self.assertEqual(api_key(p, {"TOLLGATE_MODELS_X_KEY": "  ", "X_API_KEY": "std"}), "std")
        self.assertIsNone(api_key(p, {}))
        self.assertIsNone(api_key(p, {"TOLLGATE_MODELS_X_KEY": "", "X_API_KEY": ""}))
        self.assertIsNone(api_key(p, {"OTHER": "x"}))

    def test_real_gemini_order(self):
        gemini = load_providers(ROOT)["gemini"]
        both = {"GEMINI_API_KEY": "g", "GOOGLE_API_KEY": "o"}
        self.assertEqual(api_key(gemini, both), "o")
        self.assertEqual(api_key(gemini, {"GEMINI_API_KEY": "g"}), "g")
        self.assertEqual(api_key(gemini, {**both, "TOLLGATE_MODELS_GEMINI_KEY": "d"}), "d")

    def test_unusable_values_are_skipped(self):
        p = make_provider(env=("A", "B"))
        self.assertEqual(api_key(p, {"A": "bad\nvalue", "B": "ok"}), "ok")
        self.assertEqual(api_key(p, {"A": "chiaveè", "B": "ok"}), "ok")


class ClientTest(NetCase):
    def run_fetch(self, provider, opener, key=KEY, seconds=60, **kw):
        return fetch_pages(provider, key, deadline=Deadline(seconds), opener=opener, **kw)

    def test_bearer_and_version_headers(self):
        p = make_provider(headers={"anthropic-version": "2026-10-21"})
        opener = FakeOpener(FakeResponse({"data": []}))
        self.assertEqual(self.run_fetch(p, opener), [{"data": []}])
        (req,) = opener.requests
        h = headers_of(req)
        self.assertEqual(h["authorization"], f"Bearer {KEY}")
        self.assertEqual(h["anthropic-version"], "2026-10-21")
        self.assertEqual(req.get_method(), "GET")
        self.assertIsNone(req.data)
        self.assertEqual(req.full_url, p.url)

    def test_gemini_key_in_header_not_url(self):
        p = make_provider(name="gemini", auth="x-goog-api-key", paging="gemini")
        opener = FakeOpener(FakeResponse({"models": []}))
        self.run_fetch(p, opener)
        (req,) = opener.requests
        self.assertEqual(headers_of(req)["x-goog-api-key"], KEY)
        self.assertNotIn("authorization", headers_of(req))
        self.assertNotIn(KEY, req.full_url)
        self.assertNotIn("key=", req.full_url.lower())

    def test_timeout_is_capped_by_deadline(self):
        opener = FakeOpener(FakeResponse({"data": []}))
        self.run_fetch(make_provider(), opener, seconds=2.0, timeout=5.0)
        self.assertLessEqual(opener.timeouts[0], 2.0)
        opener = FakeOpener(FakeResponse({"data": []}))
        self.run_fetch(make_provider(), opener, seconds=60, timeout=5.0)
        self.assertEqual(opener.timeouts[0], 5.0)

    def test_response_is_closed(self):
        resp = FakeResponse({"data": []})
        self.run_fetch(make_provider(), FakeOpener(resp))
        self.assertTrue(resp.closed)

    def test_anthropic_pages_followed(self):
        p = make_provider(paging="anthropic")
        first = {"data": [{"id": "a"}], "has_more": True, "last_id": "a"}
        second = {"data": [{"id": "b"}], "has_more": False, "last_id": "b"}
        opener = FakeOpener(FakeResponse(first), FakeResponse(second))
        self.assertEqual(self.run_fetch(p, opener), [first, second])
        self.assertEqual(len(opener.requests), 2)
        q1 = parse_qs(urlsplit(opener.requests[0].full_url).query)
        q2 = parse_qs(urlsplit(opener.requests[1].full_url).query)
        self.assertNotIn("after_id", q1)
        self.assertEqual(q1["limit"], ["1000"])
        self.assertEqual(q2["after_id"], ["a"])
        self.assertEqual(q2["limit"], ["1000"])

    def test_anthropic_stops_without_has_more(self):
        p = make_provider(paging="anthropic")
        opener = FakeOpener(FakeResponse({"data": [], "has_more": False, "last_id": "a"}))
        self.assertEqual(len(self.run_fetch(p, opener)), 1)
        opener = FakeOpener(FakeResponse({"data": [], "has_more": True}))
        self.assertEqual(len(self.run_fetch(p, opener)), 1)

    def test_gemini_pages_followed(self):
        p = make_provider(name="gemini", paging="gemini", auth="x-goog-api-key",
                          url="https://api.example.invalid/v1beta/models?pageSize=1000")
        first = {"models": [{"name": "models/a"}], "nextPageToken": "tok 1/="}
        second = {"models": [{"name": "models/b"}]}
        opener = FakeOpener(FakeResponse(first), FakeResponse(second))
        self.assertEqual(self.run_fetch(p, opener), [first, second])
        q2 = parse_qs(urlsplit(opener.requests[1].full_url).query)
        self.assertEqual(q2["pageToken"], ["tok 1/="])
        self.assertEqual(q2["pageSize"], ["1000"])
        self.assertNotIn("pageToken", urlsplit(opener.requests[0].full_url).query)

    def test_page_cap(self):
        p = make_provider(paging="anthropic")
        pages = [FakeResponse({"data": [], "has_more": True, "last_id": f"id{i}"})
                 for i in range(11)]
        opener = FakeOpener(*pages)
        with self.assertRaises(FetchError) as cm:
            self.run_fetch(p, opener)
        self.assertEqual(str(cm.exception), "troppe pagine")
        self.assertEqual(len(opener.requests), 10)

    def test_exactly_max_pages_is_fine(self):
        p = make_provider(paging="anthropic")
        pages = [FakeResponse({"data": [], "has_more": i < 9, "last_id": f"id{i}"})
                 for i in range(10)]
        self.assertEqual(len(self.run_fetch(p, FakeOpener(*pages))), 10)

    def test_fetch_errors_are_fetch_errors(self):
        def http(code):
            return HTTPError("https://api.example.invalid/v1/models", code, "x", {}, None)

        cases = [
            (http(401), "chiave rifiutata"),
            (http(403), "chiave rifiutata"),
            (http(429), "troppe richieste"),
            (http(500), "errore HTTP 500"),
            (http(404), "errore HTTP 404"),
            (http(302), "redirect rifiutato"),
            (TimeoutError("lento"), "tempo scaduto"),
            (URLError(TimeoutError("lento")), "tempo scaduto"),
            (URLError("niente dns"), "nessuna risposta"),
            (ConnectionResetError("reset"), "nessuna risposta"),
            (FakeResponse(raw=b"<html><body>no</body></html>"), "risposta non JSON"),
            (FakeResponse(raw=b"{rotto"), "risposta non JSON"),
            (FakeResponse(raw=b"\xff\xfe"), "risposta non JSON"),
            (FakeResponse({"data": []}, status=500), "errore HTTP 500"),
            (FakeResponse({"data": []}, status=301), "redirect rifiutato"),
        ]
        for outcome, text in cases:
            with self.subTest(text=text, outcome=repr(outcome)):
                with self.assertRaises(FetchError) as cm:
                    self.run_fetch(make_provider(), FakeOpener(outcome))
                self.assertEqual(str(cm.exception), text)

    def test_redirect_refused(self):
        opener = build_opener()
        handlers = [h for h in opener.handlers if isinstance(h, urllib.request.HTTPRedirectHandler)]
        self.assertEqual(len(handlers), 1)
        req = urllib.request.Request("https://api.example.invalid/v1/models")
        for code in (301, 302, 303, 307, 308):
            with self.subTest(code=code):
                with self.assertRaises(FetchError) as cm:
                    handlers[0].redirect_request(req, None, code, "x", {},
                                                 "https://altro.invalid/")
                self.assertEqual(str(cm.exception), "redirect rifiutato")
                with self.assertRaises(FetchError) as cm:
                    getattr(handlers[0], f"http_error_{code}")(req, None, code, "x", {})
                self.assertEqual(str(cm.exception), "redirect rifiutato")

    def test_opener_handles_only_https(self):
        opener = build_opener()
        self.assertIsInstance(opener, urllib.request.OpenerDirector)
        for scheme in ("http", "file", "ftp", "data"):
            with self.subTest(scheme=scheme):
                self.assertNotIn(scheme, opener.handle_open)
        self.assertIn("https", opener.handle_open)
        self.assertEqual(sorted(type(h).__name__ for h in opener.handlers),
                         ["HTTPDefaultErrorHandler", "HTTPErrorProcessor", "HTTPSHandler",
                          "UnknownHandler", "_RefuseRedirect"])
        self.assertFalse(any(hasattr(h, "proxy_open") for h in opener.handlers))

    def test_opener_refuses_other_schemes_without_network(self):
        opener = build_opener()
        for url in ("http://api.example.invalid/", "file:///etc/hostname",
                    "ftp://api.example.invalid/"):
            with self.subTest(url=url):
                with self.assertRaises(URLError):
                    opener.open(url, timeout=1)

    def test_environment_proxy_ignored(self):
        with mock.patch.dict(os.environ, {"https_proxy": "http://proxy.invalid:3128",
                                          "HTTPS_PROXY": "http://proxy.invalid:3128",
                                          "http_proxy": "http://proxy.invalid:3128"}):
            opener = build_opener()
        self.assertFalse(any(isinstance(h, urllib.request.ProxyHandler) and h.proxies
                             for h in opener.handlers))
        self.assertFalse(any(hasattr(h, "proxy_open") for h in opener.handlers))
        self.assertEqual([type(h) for h in opener.handle_open["https"]],
                         [urllib.request.HTTPSHandler])

    def test_deeply_nested_json_is_fetch_error(self):
        body = b"[" * 200_000 + b"]" * 200_000
        with self.assertRaises(FetchError) as cm:
            self.run_fetch(make_provider(), FakeOpener(FakeResponse(raw=body)))
        self.assertEqual(str(cm.exception), "risposta non JSON")
        self.assertIsNone(cm.exception.__context__)
        self.assertIsNone(cm.exception.__cause__)

    def test_redirect_handler_closes_response(self):
        handler = next(h for h in build_opener().handlers
                       if isinstance(h, urllib.request.HTTPRedirectHandler))
        req = urllib.request.Request("https://api.example.invalid/v1/models")
        for call in (lambda fp: handler.redirect_request(req, fp, 302, "x", {}, "https://a.invalid/"),
                     lambda fp: handler.http_error_302(req, fp, 302, "x", {})):
            fp = FakeResponse({})
            with self.assertRaises(FetchError):
                call(fp)
            self.assertTrue(fp.closed)

    def test_default_opener_built_at_call_time(self):
        opener = FakeOpener(FakeResponse({"data": []}))
        with mock.patch.object(modelsfetch, "build_opener", return_value=opener) as built:
            fetch_pages(make_provider(), KEY, deadline=Deadline(60))
        built.assert_called_once_with()
        self.assertEqual(len(opener.requests), 1)

    def test_other_host_refused(self):
        p = make_provider(url="https://altro.invalid/v1/models")
        opener = FakeOpener(FakeResponse({"data": []}))
        with self.assertRaises(FetchError) as cm:
            self.run_fetch(p, opener)
        self.assertEqual(str(cm.exception), "host diverso da quello del fornitore")
        self.assertEqual(opener.requests, [])

    def test_non_https_url_refused(self):
        p = make_provider(url="http://api.example.invalid/v1/models")
        opener = FakeOpener(FakeResponse({"data": []}))
        with self.assertRaises(FetchError):
            self.run_fetch(p, opener)
        self.assertEqual(opener.requests, [])

    def test_body_over_cap_stops(self):
        resp = EndlessResponse()
        with self.assertRaises(FetchError) as cm:
            self.run_fetch(make_provider(), FakeOpener(resp), max_bytes=100_000)
        self.assertEqual(str(cm.exception), "risposta troppo grande")
        self.assertLessEqual(resp.total, 100_001)
        small = FakeResponse(raw=b"[" + b" " * 50 + b"]")
        self.assertEqual(self.run_fetch(make_provider(), FakeOpener(small), max_bytes=100),
                         [[]])
        big = FakeResponse(raw=b"[" + b" " * 200 + b"]")
        with self.assertRaises(FetchError):
            self.run_fetch(make_provider(), FakeOpener(big), max_bytes=100)

    def test_deadline_class(self):
        clk = FakeClock()
        d = Deadline(10, clock=clk)
        self.assertEqual(d.left(), 10)
        d.check()
        clk.t += 4
        self.assertEqual(d.left(), 6)
        clk.t += 6
        self.assertEqual(d.left(), 0)
        with self.assertRaises(FetchError) as cm:
            d.check()
        self.assertEqual(str(cm.exception), "tempo scaduto")
        clk.t += 100
        self.assertEqual(d.left(), 0)

    def test_deadline_stops_between_chunks_and_pages(self):
        clk = FakeClock()
        resp = EndlessResponse()
        resp.on_read = lambda chunk: setattr(clk, "t", clk.t + 100)
        with self.assertRaises(FetchError) as cm:
            fetch_pages(make_provider(), KEY, deadline=Deadline(10, clock=clk),
                        opener=FakeOpener(resp))
        self.assertEqual(str(cm.exception), "tempo scaduto")
        self.assertLessEqual(resp.total, 64 * 1024)

        clk = FakeClock()
        p = make_provider(paging="anthropic")
        first = FakeResponse({"data": [], "has_more": True, "last_id": "a"})
        # la scadenza passa quando la prima pagina è finita (ultima lettura vuota)
        first.on_read = lambda chunk: None if chunk else setattr(clk, "t", clk.t + 100)
        opener = FakeOpener(first, FakeResponse({"data": []}))
        with self.assertRaises(FetchError) as cm:
            fetch_pages(p, KEY, deadline=Deadline(10, clock=clk), opener=opener)
        self.assertEqual(str(cm.exception), "tempo scaduto")
        self.assertEqual(len(opener.requests), 1)

        clk = FakeClock()
        d = Deadline(10, clock=clk)
        clk.t += 50
        opener = FakeOpener(FakeResponse({"data": []}))
        with self.assertRaises(FetchError):
            fetch_pages(p, KEY, deadline=d, opener=opener)
        self.assertEqual(opener.requests, [])

    def test_key_never_in_errors_lines_or_cache(self):
        url = f"https://api.example.invalid/v1/models?key={KEY}"
        outcomes = [
            URLError(f"boom {KEY}"),
            HTTPError(url, 500, f"errore {KEY}", {"X-Echo": KEY, "Authorization": KEY}, None),
            HTTPError(url, 401, f"errore {KEY}", {"X-Echo": KEY}, None),
            ValueError(f"intestazione non valida {KEY}"),
            OSError(f"socket {KEY}"),
            FakeResponse(raw=f"<html>{KEY}</html>".encode()),
        ]
        for outcome in outcomes:
            with self.subTest(outcome=type(outcome).__name__):
                with self.assertRaises(FetchError) as cm:
                    self.run_fetch(make_provider(), FakeOpener(outcome))
                err = cm.exception
                self.assertNotIn(KEY, str(err))
                self.assertNotIn(KEY, repr(err))
                self.assertIsNone(err.__context__)
                self.assertIsNone(err.__cause__)
                self.assertEqual(err.args, (str(err),))

        state = TempState()
        self.addCleanup(state.cleanup)
        p = make_provider()
        page = {"data": [{"id": "claude-x-1"}]}
        cached_pages(state.state, p, KEY, now=T0, deadline=Deadline(60),
                     validate=lambda pages: None,
                     fetch=lambda provider, key, *, deadline: [page])
        cache_files = list((state.dir / "models").iterdir())
        self.assertEqual(len(cache_files), 1)
        self.assertNotIn(KEY, cache_files[0].read_text(encoding="utf-8"))

    def test_fetch_error_raised_inside_opener_is_reraised_clean(self):
        class Raiser:
            def open(self, request, timeout=None):
                try:
                    raise URLError(f"x {KEY}")
                except URLError:
                    raise FetchError("redirect rifiutato")

        with self.assertRaises(FetchError) as cm:
            self.run_fetch(make_provider(), Raiser())
        self.assertIsNone(cm.exception.__context__)
        self.assertIsNone(cm.exception.__cause__)


class CacheTest(NetCase):
    def setUp(self):
        super().setUp()
        self.ts = TempState()
        self.addCleanup(self.ts.cleanup)
        self.state = self.ts.state
        self.provider = make_provider(name="openai")
        self.pages = [{"data": [{"id": "gpt-5"}]}]
        self.path = self.ts.dir / "models" / "openai.json"
        self.calls = 0

    def fetch(self, provider, key, *, deadline):
        self.calls += 1
        return self.pages

    def failing(self, text):
        def fetch(provider, key, *, deadline):
            self.calls += 1
            raise FetchError(text)
        return fetch

    def run_cached(self, now=T0, validate=None, **kw):
        kw.setdefault("fetch", self.fetch)
        kw.setdefault("deadline", Deadline(60))
        return cached_pages(self.state, self.provider, KEY, now=now,
                            validate=validate or (lambda pages: None), **kw)

    def write_cache(self, fetched_at, pages=None):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps({"fetched_at": clock.fmt(fetched_at),
                                         "pages": self.pages if pages is None else pages}),
                             encoding="utf-8")

    def test_network_result_is_written(self):
        pages, note = self.run_cached()
        self.assertEqual((pages, note, self.calls), (self.pages, None, 1))
        data = json.loads(self.path.read_text(encoding="utf-8"))
        self.assertEqual(data["pages"], self.pages)
        self.assertEqual(clock.parse(data["fetched_at"]), T0)

    def test_cache_fresh_used(self):
        self.run_cached()
        pages, note = self.run_cached(now=T0 + timedelta(hours=23),
                                      fetch=self.failing("non deve essere chiamata"))
        self.assertEqual(pages, self.pages)
        self.assertEqual(note, "elenco dalla cache del 2026-11-04")
        self.assertEqual(self.calls, 1)

    def test_cache_stale_refetched(self):
        self.run_cached()
        pages, note = self.run_cached(now=T0 + timedelta(hours=25))
        self.assertEqual((pages, note, self.calls), (self.pages, None, 2))
        data = json.loads(self.path.read_text(encoding="utf-8"))
        self.assertEqual(clock.parse(data["fetched_at"]), T0 + timedelta(hours=25))

    def test_corrupt_cache_refetched(self):
        for text in ("non json", "[]", '{"fetched_at": 3, "pages": []}',
                     '{"fetched_at": "ieri", "pages": []}',
                     json.dumps({"fetched_at": clock.fmt(T0), "pages": "x"}),
                     json.dumps({"fetched_at": clock.fmt(T0), "pages": [1]})):
            with self.subTest(text=text):
                self.path.parent.mkdir(parents=True, exist_ok=True)
                self.path.write_text(text, encoding="utf-8")
                before = self.calls
                pages, note = self.run_cached()
                self.assertEqual((pages, note, self.calls), (self.pages, None, before + 1))

    def test_cache_failing_validation_is_refetched(self):
        self.write_cache(T0, pages=[{"data": "storto"}])

        def validate(pages):
            if pages != self.pages:
                raise ModelsFormatError("storto")

        pages, note = self.run_cached(validate=validate)
        self.assertEqual((pages, note, self.calls), (self.pages, None, 1))

    def test_refresh_ignores_cache(self):
        self.run_cached()
        pages, note = self.run_cached(now=T0 + timedelta(hours=1), refresh=True)
        self.assertEqual((note, self.calls), (None, 2))

    def test_failed_fetch_keeps_and_uses_cache(self):
        self.write_cache(T0 - timedelta(days=3))
        before = self.path.read_bytes()
        pages, note = self.run_cached(fetch=self.failing("errore HTTP 500"))
        self.assertEqual(pages, self.pages)
        self.assertEqual(note, "rete non riuscita (errore HTTP 500), elenco dalla cache del "
                               "2026-11-01")
        self.assertEqual(self.path.read_bytes(), before)

    def test_failed_refresh_uses_cache(self):
        self.write_cache(T0 - timedelta(hours=1))
        pages, note = self.run_cached(fetch=self.failing("tempo scaduto"), refresh=True)
        self.assertEqual(note, "rete non riuscita (tempo scaduto), elenco dalla cache del "
                               "2026-11-04")

    def test_failed_fetch_without_cache_raises(self):
        with self.assertRaises(FetchError) as cm:
            self.run_cached(fetch=self.failing("nessuna risposta"))
        self.assertEqual(str(cm.exception), "nessuna risposta")
        self.assertFalse(self.path.exists())

    def test_expired_deadline_uses_cache_without_fetch(self):
        for age, prefix in ((timedelta(hours=1), ""),
                            (timedelta(days=3), "rete non riuscita (tempo scaduto), ")):
            with self.subTest(age=age):
                self.write_cache(T0 - age)
                before = self.path.read_bytes()
                pages, note = self.run_cached(fetch=self.failing("non deve essere chiamata"),
                                              deadline=Deadline(-1))
                self.assertEqual(pages, self.pages)
                self.assertEqual(note, f"{prefix}elenco dalla cache del {T0 - age:%Y-%m-%d}")
                self.assertEqual((self.calls, self.path.read_bytes()), (0, before))

    def test_expired_deadline_without_cache_is_skipped(self):
        with self.assertRaises(DeadlineSkipped):
            self.run_cached(fetch=self.failing("non deve essere chiamata"), deadline=Deadline(-1))
        self.assertEqual(self.calls, 0)
        self.assertFalse(self.path.exists())
        self.assertTrue(issubclass(DeadlineSkipped, FetchError))

    def test_bad_shape_from_network_falls_back_to_cache(self):
        self.write_cache(T0 - timedelta(days=3))
        before = self.path.read_bytes()

        def validate(pages):
            if pages == self.bad:
                raise ModelsFormatError("storto")

        self.bad = [{"data": "storto"}]
        for refresh in (False, True):
            with self.subTest(refresh=refresh):
                pages, note = self.run_cached(validate=validate, refresh=refresh,
                                              fetch=lambda p, k, *, deadline: self.bad)
                self.assertEqual(pages, self.pages)
                self.assertEqual(note, "rete non riuscita (forma inattesa), elenco dalla cache "
                                       "del 2026-11-01")
                self.assertEqual(self.path.read_bytes(), before)

    def test_cache_written_atomically(self):
        real_replace = os.replace
        seen = []

        def spy(src, dst):
            seen.append((Path(src).name, Path(dst).name, Path(src).exists()))
            return real_replace(src, dst)

        with mock.patch("os.replace", spy):
            self.run_cached()
        self.assertEqual(len(seen), 1)
        src, dst, existed = seen[0]
        self.assertEqual(dst, "openai.json")
        self.assertNotEqual(src, dst)
        self.assertTrue(existed)
        self.assertEqual([p.name for p in self.path.parent.iterdir()], ["openai.json"])

    def test_cache_temp_names_are_unique_and_removed_on_failure(self):
        names = []
        real_replace = os.replace

        def spy(src, dst):
            names.append(Path(src).name)
            return real_replace(src, dst)

        with mock.patch("os.replace", spy):
            self.run_cached()
            self.run_cached(now=T0 + timedelta(hours=30))
        self.assertEqual(len(names), 2)
        self.assertNotEqual(names[0], names[1])
        self.assertNotEqual(names[0], ".openai.json.tmp")
        self.assertEqual([p.name for p in self.path.parent.iterdir()], ["openai.json"])

    def test_cache_write_failure_does_not_break_result(self):
        with mock.patch("os.replace", side_effect=OSError("pieno")):
            pages, note = self.run_cached()
        self.assertEqual((pages, note), (self.pages, None))
        self.assertEqual([p.name for p in self.path.parent.iterdir()], [])

    def test_cache_not_written_when_validate_fails(self):
        def validate(pages):
            raise ModelsFormatError("storto")

        with self.assertRaises(ModelsFormatError):
            self.run_cached(validate=validate)
        self.assertFalse(self.path.exists())

    def test_validate_failure_keeps_old_cache(self):
        self.write_cache(T0 - timedelta(days=2))
        before = self.path.read_bytes()

        def validate(pages):
            raise ModelsFormatError("storto")

        with self.assertRaises(ModelsFormatError):
            self.run_cached(validate=validate)
        self.assertEqual(self.path.read_bytes(), before)

    def test_future_cache_is_stale(self):
        self.write_cache(T0 + timedelta(hours=1))
        pages, note = self.run_cached()
        self.assertEqual((pages, note, self.calls), (self.pages, None, 1))

    def test_patched_fetch_is_used(self):
        with mock.patch("tollgate_flow.modelsfetch.fetch_pages",
                        return_value=self.pages) as patched:
            deadline = Deadline(60)
            pages, note = cached_pages(self.state, self.provider, KEY, now=T0, deadline=deadline,
                                       validate=lambda pages: None)
        self.assertEqual((pages, note), (self.pages, None))
        patched.assert_called_once_with(self.provider, KEY, deadline=deadline)


class LayersTest(unittest.TestCase):
    def sources(self):
        for package in ("tollgate_hooks", "tollgate_checks"):
            for path in sorted((BIN / package).glob("*.py")):
                yield package, path, path.read_text(encoding="utf-8")

    def test_hooks_do_not_reach_models_net(self):
        count = 0
        for package, path, source in self.sources():
            count += 1
            for name in imported_modules(source, package):
                with self.subTest(file=f"{package}/{path.name}", imported=name):
                    self.assertFalse(name.startswith("tollgate_flow"), name)
                    self.assertNotIn("modelsfetch", name)
                    self.assertNotIn("models_check", name)
            with self.subTest(file=f"{package}/{path.name}", what="testo"):
                self.assertNotIn("modelsfetch", source)
                self.assertNotIn("models_check", source)
        self.assertGreater(count, 20)
        text = (ROOT / "hooks" / "run").read_text(encoding="utf-8")
        self.assertNotIn("modelsfetch", text)
        self.assertNotIn("models_check", text)

    def test_hook_run_does_not_load_models_net(self):
        mods = ["tollgate_checks." + p.stem for p in (BIN / "tollgate_checks").glob("*.py")
                if p.stem != "__init__"]
        code = (
            "import importlib, sys\n"
            f"sys.path.insert(0, {str(BIN)!r})\n"
            "import tollgate_core.cli, tollgate_hooks.runner\n"
            f"for m in {mods!r}:\n"
            "    importlib.import_module(m)\n"
            "print('tollgate_flow.modelsfetch' in sys.modules)\n")
        env = {k: v for k, v in os.environ.items() if k not in helpers.MODEL_KEY_VARS}
        r = subprocess.run([sys.executable, "-B", "-c", code], capture_output=True, text=True,
                           timeout=60, env=env, cwd=tempfile.gettempdir())
        self.assertEqual((r.returncode, r.stdout.strip()), (0, "False"), r.stderr)


class NoNetworkHelperTest(unittest.TestCase):
    def test_no_network_helper(self):
        real_socket, real_connect = socket.socket, socket.create_connection
        real_resolve = socket.getaddrinfo
        with mock.patch.dict(os.environ, {name: "valore-finto" for name in helpers.MODEL_KEY_VARS}):
            with no_network():
                for name in helpers.MODEL_KEY_VARS:
                    self.assertNotIn(name, os.environ)
                with self.assertRaises(AssertionError):
                    socket.create_connection(("127.0.0.1", 9), timeout=1)
                with self.assertRaises(AssertionError):
                    socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                with self.assertRaises(AssertionError):
                    socket.getaddrinfo("esempio.invalid", 443)
                self.assertTrue(issubclass(socket.socket, real_socket))
            for name in helpers.MODEL_KEY_VARS:
                self.assertEqual(os.environ[name], "valore-finto")
        self.assertIs(socket.socket, real_socket)
        self.assertIs(socket.create_connection, real_connect)
        self.assertIs(socket.getaddrinfo, real_resolve)


if __name__ == "__main__":
    unittest.main()
