### Task 16: Regole su Bash (7.4) ed effetti esterni (8.5)

**Files:**
- Create: `bin/tollgate_checks/bash_rules.py`
- Create: `bin/tollgate_checks/effects.py`
- Test: `tests/test_check_bash.py`, `tests/test_check_effects.py`

**Interfaces:**
- Consumes: `bash.*`, `protected.is_protected`, `effects.*`, `acts.find_usable`, `git.*`, `_common.*`.
- Produces:
  - Modulo `bash_rules` (evento `pre_bash`, ordine 20): tutte le righe di 7.4 tranne `git commit` (Task 17) e gli effetti; comandi illeggibili cercati per testo (Review Focus 1).
  - Modulo `effects` (eventi `pre_bash` e `pre_mcp`, ordine 30): veto con l'identificativo della decisione 14, una esecuzione per atto `approve effect <id>`, avviso «già eseguito alle…» sullo stesso SHA (criterio 23). `bin/tollgate` del plugin non è mai un effetto.

- [ ] **Step 1: Test delle regole**

`tests/test_check_bash.py`:

```python
import shutil
import tempfile
import unittest
from pathlib import Path

from tests.hookkit import Lab
from tests.helpers import ROOT, git, make_repo


class BoundSessionTest(unittest.TestCase):
    def setUp(self):
        self.lab = Lab()

    def tearDown(self):
        self.lab.close()

    def code(self, command, **kw):
        return self.lab.bash(command, **kw).exit

    def test_push_and_pr_denied(self):
        self.assertEqual(self.code("git push origin tg/7-demo"), 2)
        self.assertEqual(self.code("gh pr create --fill"), 2)
        self.assertEqual(self.code("bash -c 'git push'"), 2)

    def test_branch_changes_in_worktree(self):
        for cmd in ("git switch -c altro", "git checkout -B altro", "git branch -m nuovo",
                    "git checkout main"):
            with self.subTest(cmd=cmd):
                self.assertEqual(self.code(cmd), 2)
        self.assertEqual(self.code("git checkout -- src/app.py"), 0)
        self.assertEqual(self.code("git status"), 0)

    def test_main_checkout(self):
        self.assertEqual(self.code(f"cd '{self.lab.main}' && touch x.txt"), 2)
        self.assertEqual(self.code(f"cd '{self.lab.main}' && gh pr create"), 2)
        self.assertEqual(self.code(f"echo x > '{self.lab.main}/src/app.py'"), 2)
        self.assertEqual(self.code(f"git -C '{self.lab.main}' status"), 0)

    def test_coordinator_code_writes(self):
        self.assertEqual(self.code("echo x > src/app.py"), 2)
        self.assertEqual(self.code("sed -i 's/a/b/' src/app.py"), 2)
        self.assertEqual(self.code("echo x > src/app.py", agent_id="a1"), 0)
        self.assertEqual(self.code("echo x > docs/superpowers/n.md"), 0)

    def test_destructive_and_forbidden(self):
        for cmd in ("git push -f origin tg/7-demo", "git reset --hard HEAD~1",
                    "git commit --no-verify -m x", "rm -rf /tmp/qualcosa", "claude -p ciao",
                    "TOLLGATE_STATE=/tmp ls", f"'{ROOT}/bin/tollgate' hook PreToolUse",
                    "echo x > tollgate.toml", "echo x >> .tollgate/waivers/7.toml"):
            with self.subTest(cmd=cmd):
                self.assertEqual(self.code(cmd, agent_id="a1"), 2)
        self.assertEqual(self.code("rm -rf build", agent_id="a1"), 0)

    def test_unparsable_dangerous_text(self):
        self.assertEqual(self.code("echo 'x; git push --force"), 2)
        self.assertEqual(self.code("echo 'ciao"), 0)

    def test_l0_coordinator_writes(self):
        lab = Lab(level="L0")
        try:
            self.assertEqual(lab.bash("echo x > src/app.py").exit, 0)
        finally:
            lab.close()


class RepoLevelTest(unittest.TestCase):
    def setUp(self):
        self.lab = Lab(bind=False)

    def tearDown(self):
        self.lab.close()

    def code(self, command):
        return self.lab.bash(command, cwd=self.lab.main, session_id="altra").exit

    def test_push_to_default_branch(self):
        self.assertEqual(self.code("git push origin main"), 2)
        self.assertEqual(self.code("git push"), 2)

    def test_work_branch_and_worktree_protection(self):
        self.assertEqual(self.code("git merge tg/7-demo"), 2)
        self.assertEqual(self.code("git branch -D tg/7-demo"), 2)
        self.assertEqual(self.code(f"git worktree remove '{self.lab.wt}'"), 2)
        self.assertEqual(self.code("git worktree add ../doppio tg/7-demo"), 2)
        self.assertEqual(self.code("git log --oneline"), 0)

    def test_inactive_repo_push_passes(self):
        tmp = Path(tempfile.mkdtemp(prefix="tollgate-inattivo-"))
        try:
            repo = make_repo(tmp / "r")
            r = self.lab.bash("git push origin main", cwd=repo, session_id="altra")
            self.assertEqual(r.exit, 0)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


class OrphanBashTest(unittest.TestCase):
    def test_writes_denied_reads_allowed(self):
        lab = Lab(work=False)
        try:
            r = lab.bash("git commit -am x")
            self.assertEqual(r.exit, 2)
            self.assertIn("/tollgate:adopt #7", r.stderr)
            self.assertEqual(lab.bash("git status").exit, 0)
        finally:
            lab.close()


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Test degli effetti**

`tests/test_check_effects.py`:

```python
import re
import unittest

from tests.hookkit import DEFAULT_TOML, DEFAULT_FILES, SESSION, Lab, sample
from tests.helpers import ROOT

EID = re.compile(r"approve effect (e-[0-9a-f]{8})")


def approve(lab, eid):
    lab.hook(sample("UserPromptExpansion-none", session_id=SESSION, cwd=str(lab.wt),
                    command_name="tollgate:approve", command_args=f"effect {eid}",
                    prompt=f"/tollgate:approve effect {eid}"))


class EffectsTest(unittest.TestCase):
    def setUp(self):
        self.lab = Lab(toml=DEFAULT_TOML + '[external_effects]\nallow = ["npm publish --dry-run"]\n'
                       'mcp_allow = ["mcp__lettura__*"]\n',
                       files=dict(DEFAULT_FILES, **{"scripts/ok.sh": "echo ok\n"}))

    def tearDown(self):
        self.lab.close()

    def test_veto_act_once_then_warning(self):
        r = self.lab.bash("npm publish")
        self.assertEqual(r.exit, 2)
        eid = EID.search(r.stderr).group(1)
        approve(self.lab, eid)
        self.assertEqual(self.lab.bash("npm publish").exit, 0)
        self.assertEqual(len(self.lab.events("effect_executed")), 1)
        r = self.lab.bash("npm publish")
        self.assertEqual(r.exit, 2)
        self.assertIn("già eseguito alle", r.stderr)
        self.assertEqual(EID.search(r.stderr).group(1), eid)

    def test_other_effects(self):
        for cmd in ("gh pr edit 3 --title x", "gh api graphql -f query='mutation { x }'",
                    "curl -X POST https://example.invalid", "bash scripts/nuovo.sh"):
            with self.subTest(cmd=cmd):
                if cmd.endswith("nuovo.sh"):
                    (self.lab.wt / "scripts/nuovo.sh").write_text("echo x\n")
                self.assertEqual(self.lab.bash(cmd, agent_id="a1").exit, 2)

    def test_allowed(self):
        for cmd in ("npm publish --dry-run", "bash scripts/ok.sh", "gh pr view 3",
                    f"'{ROOT}/bin/tollgate' verify"):
            with self.subTest(cmd=cmd):
                self.assertEqual(self.lab.bash(cmd, agent_id="a1").exit, 0)

    def test_mcp(self):
        p = self.lab._base("PreToolUse-Bash", None, None, tool_name="mcp__srv__scrivi",
                           tool_input={"testo": "x"})
        self.assertEqual(self.lab.hook(p).exit, 2)
        p = self.lab._base("PreToolUse-Bash", None, None, tool_name="mcp__lettura__cerca",
                           tool_input={"q": "x"})
        self.assertEqual(self.lab.hook(p).exit, 0)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 3: Verificare che falliscano**

Run: `python3 -B -m unittest tests.test_check_bash tests.test_check_effects -v`
Expected: FAIL (tutto passa con uscita 0).

- [ ] **Step 4: `bash_rules.py`**

```python
"""PreToolUse Bash (spec 7.4, ambito 6.6). Best effort: il resto lo prende PostToolUse Bash."""
from __future__ import annotations

import os
from pathlib import Path

from tollgate_analysis import bash
from tollgate_analysis.protected import is_protected
from tollgate_core import git
from tollgate_hooks.model import deny

from ._common import governing_work, is_docs_md, orphan_tg, repo_key_of

CHECK = {"api": 1, "events": ["pre_bash"], "component": None, "order": 20}


def _inside(p: Path, root: Path) -> bool:
    return p == root or root in p.parents


def _abs(c: bash.Cmd, target: str) -> Path:
    return Path(os.path.normpath(os.path.join(c.cwd, os.path.expanduser(target))))


def _active_branches(ctx, repo) -> dict[str, object]:
    key = repo_key_of(repo)
    return {r["branch"]: r for r in ctx.db.execute(
        "SELECT * FROM work_items WHERE repo_key = ? AND phase <> 'closed' "
        "AND branch IS NOT NULL", (key,))}


def _repo_rules(ctx, c, edir: Path, repo: Path | None):
    argv_text = " ".join(c.argv) + " " + " ".join(c.env)
    if bash.is_claude(c):
        return "claude e i suoi alias sono negati: una sessione nuova sfuggirebbe ai guardrail"
    if "TOLLGATE_" in argv_text:
        return "le variabili TOLLGATE_ sono negate nei comandi (3.1)"
    if bash.is_tollgate_hook(c):
        return "tollgate hook lo lancia solo hooks/run"
    for t in bash.write_targets(c):
        p = _abs(c, t)
        r = git.toplevel(p)
        if is_protected(ctx.rel(p, r) if r else None, p.resolve(),
                        abs_roots=ctx.protected_roots(r)):
            return f"scrittura su un file protetto: {t}"
    d = bash.destructive(c)
    if d:
        return f"{d} è negato (7.4)"
    for t in bash.rm_rf_targets(c):
        roots = [x for x in (repo, ctx.work and ctx.work["worktree"] and
                             Path(ctx.work["worktree"]).resolve()) if x]
        if not any(_inside(Path(t).resolve(), r) for r in roots):
            return f"rm -rf fuori dal repo e dal worktree: {t}"
    if repo is None:
        return None
    default = git.default_branch(repo)
    if bash.is_push(c):
        if bash.push_is_force(c):
            return "push forzato negato: lo fanno solo open-pr e sync (6.5)"
        targets = bash.push_targets(c) or [git.branch(edir) or ""]
        if default and default in targets:
            return f"push verso {default} negato: l'hotfix passa da un ramo e da una PR (9.4)"
    works = _active_branches(ctx, repo)
    if git.branch(edir) == default and any(a in works for a in bash.merge_args(c)):
        return "merge di un ramo tg/* di un lavoro attivo verso il predefinito negato"
    if any(b in works for b in bash.branch_deletes(c)):
        return "cancellazione del ramo di un lavoro attivo negata"
    op = bash.worktree_op(c)
    if op:
        existing = git.worktrees(repo)
        if op[0] == "remove" and any(Path(op[1]).resolve() == Path(w["worktree"]).resolve()
                                     for w in works.values() if w["worktree"]):
            return "rimozione del worktree di un lavoro attivo negata"
        if op[0] == "add" and (any(Path(op[1]).resolve() == p for p, _ in existing)
                               or (op[2] and any(op[2] == b for _, b in existing))):
            return "git worktree add doppio negato"
    return None


def _work_rules(ctx, event, c, edir: Path, work):
    wt = Path(work["worktree"]).resolve() if work["worktree"] else None
    if bash.is_push(c):
        return "il push del ramo lo fa /tollgate:finish (open-pr), non Bash (6.6)"
    if bash.is_gh_pr_create(c):
        return "la PR la apre /tollgate:finish (open-pr), non gh pr create (6.6)"
    if wt is None:
        return None
    main = git.main_worktree(wt)
    in_wt = _inside(edir, wt)
    if in_wt:
        bc = bash.branch_change(c)
        if bc:
            return f"{bc} nel worktree negato: il ramo del lavoro non cambia (6.6)"
        branches = git.local_branches(wt)
        if any(a in branches or a == "-" for a in bash.checkout_args(c)):
            return "git checkout di un altro ramo nel worktree negato (6.6)"
    if _inside(edir, main) and not in_wt and bash.writes(c):
        return f"scritture nel checkout principale negate durante il lavoro #{work['issue']} (6.6)"
    for t in bash.write_targets(c):
        p = _abs(c, t).resolve()
        if _inside(p, main) and not _inside(p, wt):
            return f"scrittura nel checkout principale negata: {t}"
        if (event.agent_id is None and work["level"] in ("L1", "L2") and _inside(p, wt)
                and not is_docs_md(ctx.rel(p, wt)) and not ctx.rel(p, wt).startswith(
                    ".superpowers/")):
            return (f"in {work['level']} il codice lo scrivono gli implementatori, anche con "
                    f"redirect o sed -i: {t}")
    return None


def decide(event, ctx):
    command = str(event.tool_input.get("command") or "")
    try:
        cmds = bash.parse(command, str(event.cwd))
    except bash.BashParseError:
        label = bash.text_danger(command)
        return [deny(f"comando non leggibile che contiene «{label}»: riscrivilo in forma "
                     f"semplice", rule="bash")] if label else []
    for c in cmds:
        if not c.argv and not c.redirects:
            continue
        edir = Path(bash.effective_dir(c))
        repo = git.toplevel(edir) if edir.exists() else None
        reason = _repo_rules(ctx, c, edir, repo)
        if reason is None:
            work = governing_work(ctx, edir)
            if work is not None:
                reason = _work_rules(ctx, event, c, edir, work)
            elif bash.writes(c):
                n = orphan_tg(ctx, repo)
                if n is not None:
                    reason = (f"ramo tg/{n}-* senza lavoro nel DB: comandi che scrivono negati. "
                              f"L'utente deve lanciare /tollgate:adopt #{n} (12.4)")
        if reason:
            return [deny(reason, rule="bash")]
    return []
```

- [ ] **Step 5: `effects.py`**

```python
"""Effetti esterni (spec 8.5): veto con identificativo, una esecuzione per atto."""
from __future__ import annotations

import fnmatch
import json
from pathlib import Path

from tollgate_analysis import bash
from tollgate_core import acts, effects, git
from tollgate_hooks.model import deny, inject, record

from ._common import governing_work

CHECK = {"api": 1, "events": ["pre_bash", "pre_mcp"], "component": None, "order": 30}


def _effect(ctx, event, command: str, reason: str, repo: Path | None, where: Path):
    work = governing_work(ctx, where)
    work_id = work["id"] if work is not None else None
    sha = git.head(repo) if repo else None
    key = effects.effect_key(command, work_id, sha)
    eid = effects.effect_id(key)
    act = acts.find_usable(ctx.db, type_="approve", object_="effect", target=eid, work=work_id,
                           session=event.session, now=ctx.now)
    row = effects.get(ctx.db, key)
    if act is not None:
        out = [] if row is not None else [record("effect_request", key=key, command=command,
                                                 work=work_id, sha=sha)]
        return out + [record("effect_execute", key=key, act_id=act["act_id"], work=work_id),
                      inject(f"tollgate: effetto {eid} permesso una volta dall'atto "
                             f"{act['act_id']}")]
    prev = effects.executed_at(row)
    msg = (f"effetto esterno ({reason}): {command[:200]}. Per eseguirlo una volta l'utente "
           f"digita /tollgate:approve effect {eid}")
    if prev:
        msg += f". Attenzione: già eseguito alle {prev} su questo SHA"
    return [deny(msg, rule="effects"),
            record("effect_request", key=key, command=command, work=work_id, sha=sha)]


def _script_reason(ctx, c, edir: Path) -> str | None:
    sp = bash.script_path(c)
    if not sp:
        return None
    p = Path(sp)
    repo = git.toplevel(p)
    if repo is None:
        return None
    work = governing_work(ctx, p)
    ref = work["work_base_sha"] if work is not None and work["work_base_sha"] \
        else git.default_ref(repo)
    rel = ctx.rel(p, repo)
    if ref and rel and not git.exists_at(repo, ref, rel):
        return "script nel repo non tracciato nella base"
    return None


def decide(event, ctx):
    if event.kind == "pre_mcp":
        name = event.tool_name or ""
        if any(fnmatch.fnmatchcase(name, pat) for pat in ctx.cfg("external_effects.mcp_allow")):
            return []
        command = f"{name} {json.dumps(event.tool_input, sort_keys=True, ensure_ascii=False)}"
        return _effect(ctx, event, command, "strumento MCP non in mcp_allow", ctx.repo,
                       event.cwd)
    try:
        cmds = bash.parse(str(event.tool_input.get("command") or ""), str(event.cwd))
    except bash.BashParseError:
        return []
    ee = ctx.cfg("external_effects")
    cfg = bash.EffectsCfg(ee["commands"], ee["project_scripts"], ee["allow"])
    for c in cmds:
        if bash.uses_tollgate_bin(c, str(ctx.plugin_bin)):
            continue
        edir = Path(bash.effective_dir(c))
        reason = bash.effect_reason(c, cfg) or _script_reason(ctx, c, edir)
        if reason:
            repo = git.toplevel(edir) if edir.exists() else None
            return _effect(ctx, event, bash.normalized(c), reason, repo, edir)
    return []
```

- [ ] **Step 6: Verificare che passino**

Run: `tests/run`
Expected: OK.

- [ ] **Step 7: Commit**

```bash
git add bin/tollgate_checks/bash_rules.py bin/tollgate_checks/effects.py tests/test_check_bash.py tests/test_check_effects.py
git commit -m "tollgate P2: regole su Bash ed effetti esterni con atto una tantum"
```

---

