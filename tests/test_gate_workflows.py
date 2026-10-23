import re
import shlex
import tempfile
import unittest
from pathlib import Path

from tests.helpers import ROOT
from tollgate_analysis import workflows
from tollgate_core import VERSION
from tollgate_flow import prereq
from tollgate_gate import cli, install, protection

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


def jobs(text: str) -> dict[str, list[str]]:
    """Le righe di ogni job (chiavi a rientro 2 sotto `jobs:`)."""
    out: dict[str, list[str]] = {}
    for line in section(text, "jobs"):
        m = re.match(r"^ {2}([\w-]+):\s*$", line)
        if m:
            out[m.group(1)] = []
        elif out and (not line.strip() or indent(line) > 2):
            out[list(out)[-1]].append(line)
    return out


def effective_permissions(text: str, job: list[str]) -> dict[str, str]:
    own = section("\n".join(job), "permissions", 4)
    return mapping(own, 6) if own else mapping(section(text, "permissions"), 2)


def runs_project_commands(job: list[str]) -> bool:
    return any(re.search(r"tollgate gate (run|base-ids)\b", line) for line in run_lines("\n".join(job)))


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


PINS_FILE = ROOT / install.WORKFLOWS_DIR / "PINS"
PINNED = re.compile(r"^[\w.-]+/[\w./-]+@[0-9a-f]{40} # v\d+\.\d+\.\d+$")


def pins() -> dict[str, tuple[str, str]]:
    """`gate/workflows/PINS` (`<azione> <tag> <sha>`, una riga per azione): azione → (tag, sha)."""
    out = {}
    for line in PINS_FILE.read_text(encoding="utf-8").splitlines():
        if line.strip() and not line.startswith("#"):
            action, tag, sha = line.split()
            out[action] = (tag, sha)
    return out


def uses_of(text: str) -> list[str]:
    """Il valore di ogni `uses:` (azione, SHA e commento) del testo."""
    return [m.group(1).strip() for m in re.finditer(r"(?m)^\s*(?:- )?uses:\s*(.*)$", text)]


class PinTest(unittest.TestCase):
    def test_pins_file_format(self):
        found = pins()
        self.assertTrue(found)
        for action, (tag, sha) in found.items():
            self.assertRegex(action, r"^actions/[\w./-]+$")
            self.assertRegex(tag, r"^v\d+\.\d+\.\d+$")
            self.assertRegex(sha, r"^[0-9a-f]{40}$")

    def test_every_uses_pinned(self):
        for name in NAMES:
            found = uses_of(read(name))
            for uses in found:
                self.assertRegex(uses, PINNED, name)
        self.assertTrue(any(uses_of(read(name)) for name in NAMES))

    def test_pins_match_file(self):
        want = pins()
        used = set()
        for name in NAMES:
            for uses in uses_of(read(name)):
                ref, comment = uses.split(" # ")
                action, sha = ref.split("@")
                self.assertIn(action, want, f"{name}: {action} non è in PINS")
                self.assertEqual((comment, sha), want[action], f"{name}: {action}")
                used.add(action)
        # `setup-python` serve solo alla CI del plugin, che legge la stessa fonte
        ci = (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
        used |= {uses.split("@")[0] for uses in uses_of(ci)}
        self.assertEqual(used, set(want), "PINS ha azioni che nessun workflow usa")

    def test_no_major_tag_left(self):
        for name in NAMES:
            self.assertNotRegex(read(name), r"@v\d", name)


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
                                 ["- '__DEFAULT_BRANCH__'"], name)

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
        # `tollgate-base`: il job `ids` esegue la suite sul commit del push, senza permessi di
        # scrittura; il job di pubblicazione fa solo il checkout del predefinito (C-1)
        base = checkouts(read("base"))
        self.assertEqual([field(s, "ref") for s in base], ["${{ github.sha }}", DEFAULT_REF])
        job = jobs(read("base"))
        self.assertEqual([field(s, "ref") for s in checkouts("\n".join(job["ids"]))],
                         ["${{ github.sha }}"])
        self.assertEqual([field(s, "ref") for s in checkouts("\n".join(job["tollgate-base"]))],
                         [DEFAULT_REF])

    def test_no_job_runs_project_commands_with_write_or_token(self):
        seen = 0
        for name in NAMES:
            text = read(name)
            for key, job in jobs(text).items():
                if not runs_project_commands(job):
                    continue
                seen += 1
                perms = effective_permissions(text, job)
                self.assertNotIn("write", perms.values(), (name, key))
                self.assertNotIn("GH_TOKEN", "\n".join(job), (name, key))
                self.assertNotIn("github.token", "\n".join(job), (name, key))
        self.assertEqual(seen, 3)       # head e base di `tollgate-run`, ids di `tollgate-base`

    def test_base_ids_job_is_read_only_and_publish_job_runs_no_project_code(self):
        job = jobs(read("base"))
        self.assertEqual(sorted(job), ["ids", "tollgate-base"])
        self.assertEqual(effective_permissions(read("base"), job["ids"]), {"contents": "read"})
        self.assertEqual(effective_permissions(read("base"), job["tollgate-base"]),
                         {"contents": "read", "statuses": "write", "issues": "write"})
        publish = "\n".join(job["tollgate-base"])
        self.assertIn("needs: ids", publish)
        self.assertEqual(field(job["tollgate-base"], "if"), "always()")
        runs = run_lines(publish)
        self.assertEqual(len(runs), 1)
        self.assertIn("tollgate gate base-publish", runs[0])
        self.assertIn("--publish", runs[0])
        self.assertNotIn("base-ids", publish)
        ids_runs = "\n".join(run_lines("\n".join(job["ids"])))
        self.assertIn("gate base-ids", ids_runs)
        self.assertNotIn("--publish", ids_runs)

    def test_publish_job_name_is_the_one_protection_reads(self):
        job = jobs(read("base"))
        self.assertIn(protection.BASE_JOB, job)
        self.assertEqual(
            [k for k, lines in job.items() if "statuses" in "\n".join(
                effective_permissions(read("base"), lines)) and
             "write" in effective_permissions(read("base"), lines).values()],
            [protection.BASE_JOB])
        self.assertNotIn(protection.BASE_JOB, [field(l, "name") for l in job.values()])

    def test_verdict_has_no_condition_on_conclusion(self):
        text = read("verdict")
        for line in text.splitlines():
            if re.match(r"^\s*(?:- )?if:", line):
                self.assertNotIn("conclusion", line)
        for lines in jobs(text).values():
            self.assertIsNone(
                next((l for l in lines if re.match(r"^ {4}if:", l)), None))
        self.assertNotIn("conclusion", text)

    def test_expressions_only_in_allowed_places(self):
        for name in NAMES:
            lines = read(name).splitlines()
            for i, line in enumerate(lines):
                if EXPR not in line or line.lstrip().startswith("#"):
                    continue
                if re.match(r"^\s*(?:- )?if:", line):
                    continue
                parent = next((l.strip() for l in reversed(lines[:i])
                               if l.strip() and indent(l) < indent(line)), "")
                self.assertIn(parent, ("with:", "env:", "concurrency:"), (name, line))

    def test_run_lines_pass_the_cli_parser(self):
        seen = 0
        for name in NAMES:
            for line in run_lines(read(name)):
                if "tollgate gate " not in line:
                    continue
                words = shlex.split(re.sub(r"\$\{?[A-Z_]+\}?", "x", line))
                args = words[words.index("gate") + 1:]
                with self.subTest(name=name, args=args):
                    cli.build_parser().parse_args(args)
                seen += 1
        self.assertEqual(seen, 7)

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
        self.assertEqual(seen, 6)

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
        ids = jobs(read("base"))["ids"]
        self.assertIn(save[0], "\n".join(ids))
        # su un cache hit `ids` non ricalcola e carica comunque l'ids.json ripristinato
        compute = next(s for s in steps(read("base")) if "base-ids" in "".join(s))
        self.assertEqual(field(compute, "if"), "steps.cache.outputs.cache-hit != 'true'")
        upload = next(s for s in steps(read("base"))
                      if (field(s, "uses") or "").startswith("actions/upload-artifact@"))
        self.assertEqual(field(upload, "if"), "always()")
        self.assertEqual(field(upload, "path"), "${{ runner.temp }}/tollgate-ids/ids.json")

    def test_default_branch_placeholder_replaced(self):
        out = install.files(ROOT, default_branch="trunk", services={})
        for name in ("base", "sentinel"):
            text = out[f".github/workflows/tollgate-{name}.yml"].decode()
            self.assertNotIn("__DEFAULT_BRANCH__", text)
            self.assertEqual([l.strip() for l in section(text, "branches", 4)
                              or section("\n".join(section(text, "on")), "branches", 4)],
                             ["- 'trunk'"])
            self.assertEqual(workflows_unexpected(text), [], name)
        for bad in ("a b", "x\ny", "-x", "x: y", "'x'", "main\n"):
            with self.assertRaises(ValueError):
                install.files(ROOT, default_branch=bad, services={})

    def test_default_branch_looking_like_a_yaml_scalar_is_a_string(self):
        for branch in ("true", "123", "null", "on"):
            out = install.files(ROOT, default_branch=branch, services={})
            text = out[".github/workflows/tollgate-sentinel.yml"].decode()
            self.assertIn(f"      - '{branch}'", text.splitlines())

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
                self.assertNotIn("secrets.GITHUB_TOKEN", line, name)
                if "github.token" in line and "download-artifact" not in line:
                            self.assertRegex(line.strip(),
                                     r"^(GH_TOKEN|github-token): \$\{\{ github.token \}\}$")

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

    def test_services_go_in_every_job_that_runs_the_suite(self):
        out = install.files(ROOT, default_branch="main",
                            services={"db": "postgres:16", "cache": "redis:7"},
                            ports={"db": 5432})
        blocks = []
        for name, key in (("run", "head"), ("run", "base"), ("base", "ids")):
            text = out[f".github/workflows/tollgate-{name}.yml"].decode()
            job = jobs(text)[key]
            block = section("\n".join(job), "services", 4)
            self.assertEqual(block[:1], ["      'db':"], (name, key))
            self.assertIn("        image: 'postgres:16'", block)
            self.assertIn("        image: 'redis:7'", block)
            self.assertIn('          - "5432:5432"', block)
            blocks.append(block)
            self.assertNotIn("__SERVICES__", text)
            self.assertEqual(workflows_unexpected(text), [], name)
            self.assertEqual([k for k, lines in jobs(text).items()
                              if section("\n".join(lines), "services", 4)],
                             ["head", "base"] if name == "run" else ["ids"])
        self.assertEqual(blocks[0], blocks[1])
        self.assertEqual(blocks[0], blocks[2])
        self.assertEqual(workflows.problems(
            out[".github/workflows/tollgate-run.yml"].decode()), [])
        for name in NAMES:
            plain = install.files(ROOT, default_branch="main", services={})[
                f".github/workflows/tollgate-{name}.yml"].decode()
            self.assertNotIn("services", plain)
            self.assertNotIn("__SERVICES__", plain)

    def test_services_are_strings_in_yaml(self):
        out = install.files(ROOT, default_branch="main", services={"true": "postgres:16"})
        self.assertIn("      'true':", out[".github/workflows/tollgate-run.yml"].decode())

    def test_invalid_service_is_rejected(self):
        for name, image in (("a b", "x"), ("db", "x\n  evil: 1"), ("db", "x y"), ("db", ""),
                            ("d: b", "x"), ("db", "postgres:"), ("db", "x\n"), ("db\n", "x")):
            with self.assertRaises(ValueError, msg=(name, image)):
                install.files(ROOT, default_branch="main", services={name: image})


if __name__ == "__main__":
    unittest.main()
