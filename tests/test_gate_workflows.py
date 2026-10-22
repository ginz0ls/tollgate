import re
import tempfile
import unittest
from pathlib import Path

from tests.helpers import ROOT
from tollgate_analysis import workflows
from tollgate_core import VERSION
from tollgate_flow import prereq
from tollgate_gate import install

NAMES = ("guard", "run", "verdict", "base", "sentinel")
EXPR = "${{"
DEFAULT_REF = "${{ github.event.repository.default_branch }}"
# `problems` è scritto per i workflow del progetto, che non possono avere questi tre: nei workflow
# del gate sono voluti (9.1) e i loro permessi li fissano gli altri test
EXPECTED_PROBLEM = re.compile(r"^(usa (pull_request_target|workflow_run)|(statuses|checks): write)")
PERMISSIONS = {
    "guard": {"contents": "read", "statuses": "write", "pull-requests": "write"},
    "run": {"contents": "read"},
    "verdict": {"contents": "read", "statuses": "write", "pull-requests": "write",
                "actions": "read", "issues": "read"},
    "base": {"contents": "read", "statuses": "write", "issues": "write"},
    "sentinel": {"contents": "read", "statuses": "write", "issues": "write",
                 "pull-requests": "read"},
}
TYPES = ["opened", "synchronize", "reopened", "edited"]
EVENTS = {
    "guard": {"pull_request_target": TYPES},
    "run": {"pull_request": TYPES},
    "verdict": {"workflow_run": ["completed"]},
    "base": {"push": []},
    "sentinel": {"push": []},
}


def path_of(name: str) -> Path:
    return ROOT / install.WORKFLOWS_DIR / f"tollgate-{name}.yml"


def read(name: str) -> str:
    return path_of(name).read_text(encoding="utf-8")


def indent(line: str) -> int:
    return len(line) - len(line.lstrip(" "))


def section(text: str, key: str, at: int = 0) -> list[str]:
    """Le righe rientrate sotto `key:` (rientro `at`), fino alla prima riga meno rientrata."""
    lines, out, inside = text.splitlines(), [], False
    for line in lines:
        if not inside:
            inside = line == " " * at + f"{key}:"
            continue
        if line.strip() and indent(line) <= at:
            break
        out.append(line)
    return out


def mapping(lines: list[str], at: int) -> dict[str, str]:
    """Le chiavi `k: v` al rientro `at`."""
    out = {}
    for line in lines:
        m = re.match(r"^ {%d}([\w-]+):\s*(.*)$" % at, line)
        if m:
            out[m.group(1)] = m.group(2)
    return out


def steps(text: str) -> list[list[str]]:
    """I passi dei job (`      - ` a 6 spazi), ognuno con le sue righe."""
    out: list[list[str]] = []
    open_ = False
    for line in text.splitlines():
        if re.match(r"^ {6}- ", line):
            out.append([line])
            open_ = True
        elif open_ and (not line.strip() or indent(line) > 6):
            out[-1].append(line)
        else:
            open_ = False
    return out


def field(step: list[str], key: str) -> str | None:
    for line in step:
        m = re.match(r"^\s+(?:- )?%s:\s*(.*)$" % re.escape(key), line)
        if m:
            return m.group(1)
    return None


def run_lines(text: str) -> list[str]:
    """Il testo dei valori di `run:`, di una riga o a blocco."""
    out, lines = [], text.splitlines()
    for i, line in enumerate(lines):
        m = re.match(r"^(\s*(?:- )?)run:\s*(.*)$", line)
        if not m:
            continue
        if m.group(2) in ("|", ">", "|-", ">-"):
            base = indent(line)
            for nxt in lines[i + 1:]:
                if nxt.strip() and indent(nxt) <= base:
                    break
                out.append(nxt)
        else:
            out.append(m.group(2))
    return out


def checkouts(text: str) -> list[list[str]]:
    return [s for s in steps(text) if (field(s, "uses") or "").startswith("actions/checkout@")]


class WorkflowFilesTest(unittest.TestCase):
    def test_names_match_gate_files(self):
        gate = [f for f in prereq.GATE_FILES if f.startswith(".github/workflows/")]
        self.assertEqual(sorted(gate), sorted(f".github/workflows/tollgate-{n}.yml"
                                              for n in NAMES))
        for name in NAMES:
            self.assertTrue(path_of(name).is_file(), name)
            self.assertEqual(mapping(read(name).splitlines(), 0)["name"], f"tollgate-{name}")
        on = "\n".join(section(read("verdict"), "on"))
        self.assertEqual([l.strip() for l in section(on, "workflows", 4)], ["- tollgate-run"])

    def test_workflows_have_no_unexpected_problems(self):
        for name in NAMES:
            unexpected = [p for p in workflows.problems(read(name))
                          if not EXPECTED_PROBLEM.match(p)]
            self.assertEqual(unexpected, [], name)

    def test_permissions_exact(self):
        for name, expected in PERMISSIONS.items():
            self.assertEqual(mapping(section(read(name), "permissions"), 2), expected, name)

    def test_events_exact(self):
        for name, expected in EVENTS.items():
            lines = section(read(name), "on")
            on = "\n".join(lines)
            self.assertEqual(sorted(mapping(lines, 2)), sorted(expected), name)
            for event, types in expected.items():
                got = [l.strip()[2:] for l in section(on, "types", 4)]
                self.assertEqual(got, types, name)
            if name in ("base", "sentinel"):
                self.assertEqual([l.strip() for l in section(on, "branches", 4)],
                                 ["- __DEFAULT_BRANCH__"], name)

    def test_no_expression_in_run(self):
        for name in NAMES:
            found = run_lines(read(name))
            self.assertTrue(found, name)
            for line in found:
                self.assertNotIn(EXPR, line, name)

    def test_privileged_checkout_is_default_branch(self):
        for name in NAMES:
            if "write" not in PERMISSIONS[name].values():
                continue
            found = checkouts(read(name))
            self.assertTrue(found, name)
            for step in found:
                self.assertEqual(field(step, "persist-credentials"), "false", name)
        for name in ("guard", "verdict", "sentinel"):
            self.assertEqual([field(s, "ref") for s in checkouts(read(name))], [DEFAULT_REF], name)
        # in `tollgate-base` il secondo checkout è il commit del push, già nel predefinito, in una
        # sottocartella di dati: la CLI viene dal predefinito (`trusted`)
        base = checkouts(read("base"))
        self.assertEqual([field(s, "ref") for s in base], [DEFAULT_REF, "${{ github.sha }}"])
        self.assertEqual([field(s, "path") for s in base], ["trusted", "base"])

    def test_downloads_under_runner_temp(self):
        seen = 0
        for name in NAMES:
            for step in steps(read(name)):
                uses = field(step, "uses") or ""
                if uses.startswith("actions/download-artifact@"):
                    self.assertEqual(field(step, "continue-on-error"), "true", name)
                elif not uses.startswith("actions/cache/restore@"):
                    continue
                seen += 1
                self.assertTrue(field(step, "path").startswith("${{ runner.temp }}/"), name)
        self.assertEqual(seen, 5)

    def test_verdict_never_writes_cache(self):
        text = read("verdict")
        self.assertNotIn("cache/save", text)
        self.assertNotIn("head-ids-out", text)
        self.assertIn("actions/cache/restore@", text)

    def test_only_base_saves_cache_and_only_on_miss(self):
        for name in NAMES:
            saves = [s for s in steps(read(name))
                     if (field(s, "uses") or "").startswith("actions/cache/save@")]
            self.assertEqual(len(saves), 1 if name == "base" else 0, name)
        save = next(s for s in steps(read("base"))
                    if (field(s, "uses") or "").startswith("actions/cache/save@"))
        self.assertEqual(field(save, "if"), "steps.cache.outputs.cache-hit != 'true'")
        self.assertEqual(field(save, "key"), "tollgate-ids-${{ steps.key.outputs.tree }}")
        self.assertIn("--publish", "\n".join(run_lines(read("base"))))

    def test_default_branch_placeholder_replaced(self):
        out = install.files(ROOT, default_branch="trunk", services={})
        for name in ("base", "sentinel"):
            text = out[f".github/workflows/tollgate-{name}.yml"].decode()
            self.assertNotIn("__DEFAULT_BRANCH__", text)
            self.assertEqual([l.strip() for l in section(text, "branches", 4)
                              or section("\n".join(section(text, "on")), "branches", 4)],
                             ["- trunk"])
            self.assertEqual(workflows_unexpected(text), [], name)
        for bad in ("a b", "x\ny", "-x", "x: y", "'x'"):
            with self.assertRaises(ValueError):
                install.files(ROOT, default_branch=bad, services={})

    def test_pr_code_only_in_run_workflow(self):
        for name in NAMES:
            for step in checkouts(read(name)):
                head = "pull_request.head.sha" in (field(step, "ref") or "")
                if name != "run":
                    self.assertFalse(head, name)
                if head:
                    self.assertEqual(field(step, "persist-credentials"), "false", name)
                    self.assertEqual(field(step, "fetch-depth"), "0", name)
        for name in ("guard", "verdict", "base", "sentinel"):
            self.assertNotIn("github.event.pull_request", read(name))

    def test_run_has_no_paths_filter_and_concurrency(self):
        text = read("run")
        self.assertNotIn("paths", "\n".join(section(text, "on")))
        self.assertNotIn("branches", "\n".join(section(text, "on")))
        self.assertEqual(
            mapping(section(text, "concurrency"), 2),
            {"group": "tollgate-run-${{ github.event.pull_request.number }}",
             "cancel-in-progress": "true"})
        self.assertEqual(mapping(section(text, "permissions"), 2), {"contents": "read"})

    def test_fetch_depth_where_history_is_needed(self):
        for name in ("guard", "verdict", "sentinel", "base"):
            step = checkouts(read(name))[0]       # il primo è il predefinito (`trusted` in base)
            self.assertEqual(field(step, "fetch-depth"), "0", name)

    def test_token_only_in_env(self):
        for name in NAMES:
            text = read(name)
            for i, line in enumerate(text.splitlines()):
                if "github.token" in line and "download-artifact" not in line:
                    self.assertRegex(line.strip(), r"^(GH_TOKEN|github-token): \$\{\{ github.token \}\}$")

    def test_run_job_base_uses_trusted_cli_and_subfolder(self):
        text = read("run")
        base = "\n".join(section(text, "base", 2))
        self.assertIn("path: trusted", base)
        self.assertIn("path: base", base)
        self.assertIn("working-directory: trusted", base)
        self.assertIn('--root "$GITHUB_WORKSPACE/base"', base)
        self.assertIn("steps.cache.outputs.cache-hit != 'true'", base)
        self.assertEqual(field(next(s for s in steps(text) if "path: head" in "".join(s)),
                               "persist-credentials"), "false")


def workflows_unexpected(text: str) -> list[str]:
    return [p for p in workflows.problems(text) if not EXPECTED_PROBLEM.match(p)]


class InstallTest(unittest.TestCase):
    def test_fingerprint_stable_and_ignores_pycache(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "pkg").mkdir()
            (root / "tollgate").write_text("a")
            (root / "pkg" / "m.py").write_text("b")
            first = install.fingerprint(root)
            self.assertEqual(first, install.fingerprint(root))
            self.assertRegex(first, r"^[0-9a-f]{64}$")
            (root / "pkg" / "__pycache__").mkdir()
            (root / "pkg" / "__pycache__" / "m.cpython-311.pyc").write_bytes(b"x")
            self.assertEqual(first, install.fingerprint(root))
            (root / "pkg" / "m.py").write_text("c")
            self.assertNotEqual(first, install.fingerprint(root))

    def test_install_files_contains_gate_files_and_version(self):
        out = install.files(ROOT, default_branch="main", services={})
        for rel in prereq.GATE_FILES:
            self.assertIn(rel, out)
        self.assertEqual(out[prereq.GATE_VERSION_FILE].decode().strip(), VERSION)
        self.assertEqual(out[".github/tollgate/FINGERPRINT"].decode().strip(),
                         install.fingerprint(ROOT / "bin"))
        self.assertIn(".github/tollgate/bin/tollgate", out)
        self.assertIn(".github/tollgate/bin/tollgate_gate/install.py", out)
        self.assertFalse([p for p in out if "__pycache__" in p or p.endswith(".pyc")])
        for name in NAMES:
            self.assertEqual(workflows_unexpected(
                out[f".github/workflows/tollgate-{name}.yml"].decode()), [], name)

    def test_services_go_in_head_job_only(self):
        out = install.files(ROOT, default_branch="main",
                            services={"db": "postgres:16", "cache": "redis:7"})
        text = out[".github/workflows/tollgate-run.yml"].decode()
        head = "\n".join(section(text, "head", 2))
        self.assertEqual(section(head, "services", 4)[:1], ["      db:"])
        self.assertIn("        image: postgres:16", head)
        self.assertIn("        image: redis:7", head)
        self.assertNotIn("services", "\n".join(section(text, "base", 2)))
        self.assertNotIn("__SERVICES__", text)
        self.assertEqual(workflows_unexpected(text), [])
        self.assertEqual(workflows.problems(text), [])
        empty = install.files(ROOT, default_branch="main", services={})
        plain = empty[".github/workflows/tollgate-run.yml"].decode()
        self.assertNotIn("services", plain)
        self.assertNotIn("__SERVICES__", plain)

    def test_invalid_service_is_rejected(self):
        for name, image in (("a b", "x"), ("db", "x\n  evil: 1"), ("db", "x y"), ("db", ""),
                            ("d: b", "x")):
            with self.assertRaises(ValueError, msg=(name, image)):
                install.files(ROOT, default_branch="main", services={name: image})


if __name__ == "__main__":
    unittest.main()
