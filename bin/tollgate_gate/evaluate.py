"""Il calcolo del gate (spec 9.2, decisione 3): l'unico punto in cui si decidono le voci rosse e
quelle di `attenzione`, per `gate evaluate` su GitHub e per `finish check` in locale.

`evaluate(inputs)` costruisce un `Context` (i fatti derivati, calcolati una volta) e lo passa a
ogni famiglia di `FAMILIES`, nell'ordine. Una famiglia è una funzione `(ctx, ev) -> None` che
aggiunge voci a `ev`: per aggiungere una famiglia basta una funzione in più nell'elenco, senza
toccare le altre. Puro: legge solo git (il repo di `inputs`) e i dati ricevuti."""
from __future__ import annotations

import difflib
from functools import cached_property

from tollgate_analysis import globs, level as levelmod, mustcheck, plan as planmod, prref, waivers
from tollgate_analysis.testguard import Violation
from tollgate_core import diffcheck, git, runner
from tollgate_core.config import output_excludes

from . import l2tree
from .model import (BASE_FROM_RUN, GITHUB, CommandResult, Evaluation, GateInputs, Item)

MAX_PLAN_DIFF_LINES = 200
_RANK = {"green": 0, "empty": 1, "uncounted": 2, "red": 3}
_WAIVER_KEYS = {"test": "waiver_test", "ci": "waiver_ci", "threshold": "waiver_threshold",
                "command": "waiver_command"}


class Context:
    """I fatti che più famiglie leggono, calcolati una sola volta."""

    def __init__(self, inputs: GateInputs):
        self.inputs = inputs
        self.cfg = inputs.cfg
        self.components: dict[str, bool] = dict(inputs.cfg.get("components"))

    @property
    def is_github(self) -> bool:
        return self.inputs.where == GITHUB

    @cached_property
    def is_work(self) -> bool:
        """La PR di un lavoro di tollgate: un ramo `tg/<N>-*` (in locale, il lavoro corrente)."""
        pr = self.inputs.pr
        return prref.is_tg_branch(pr.head_ref) if pr else self.inputs.block is not None

    @cached_property
    def issue_no(self) -> int | None:
        """L'issue della PR (decisione 8): dal ramo `tg/<N>-*`, altrimenti da «Closes #N». In
        locale, senza PR, dal blocco o dall'issue letta."""
        i = self.inputs
        if i.pr is not None:
            return prref.issue_from_branch(i.pr.head_ref) or prref.closes_issue(i.pr.body)
        if i.block and isinstance(i.block.get("issue"), int):
            return i.block["issue"]
        return i.issue.number if i.issue else None

    @cached_property
    def waiver_issue(self) -> int | None:
        """L'issue le cui deroghe valgono: `issue_no` se l'issue è valida (decisione 8), altrimenti
        `None` e nessuna deroga si applica."""
        n, i = self.issue_no, self.inputs
        if n is None:
            return None
        if i.issue is None:
            return None if self.is_github else n
        if i.issue.number != n or i.issue.state != "open":
            return None
        if i.pr is not None and prref.is_tg_branch(i.pr.head_ref):
            if prref.closes_issue(i.pr.body) != n or (
                    i.block is not None and i.block.get("issue") != n):
                return None
        return n

    @cached_property
    def waiver_file(self) -> waivers.WaiverFile | None:
        """Il file delle deroghe dell'issue, solo se è dell'issue giusta e (con una PR) del ramo
        della PR (8.3)."""
        i = self.inputs
        if i.waiver_text is None or self.waiver_issue is None:
            return None
        try:
            wf = waivers.parse(i.waiver_text)
        except ValueError:
            return None
        if wf.issue != self.waiver_issue or (i.pr is not None and wf.branch != i.pr.head_ref):
            return None
        return wf

    @cached_property
    def level(self) -> str:
        """Il livello dichiarato; senza blocco `L1` (nessun controllo di livello qui)."""
        block = self.inputs.block
        return block["level"] if block and isinstance(block.get("level"), str) else "L1"

    @cached_property
    def changes(self) -> list[git.Change]:
        i = self.inputs
        return git.changes(i.repo, i.base_sha, head=i.head_sha,
                           exclude=output_excludes(self.cfg))

    @cached_property
    def files(self) -> list[str]:
        """I file toccati e non cancellati: da qui i profili attivi, come in locale."""
        return [c.path for c in self.changes if c.status != "D"]

    @cached_property
    def required(self) -> list[runner.CommandSpec]:
        """I comandi che la testa deve avere eseguito: gate globali e dei profili attivi."""
        return runner.gate_commands(self.cfg, self.files)

    @cached_property
    def results(self) -> dict[str, CommandResult]:
        return {r.name: r for r in self.inputs.commands or []}

    @cached_property
    def registered_plan(self) -> str | None:
        """Il testo del piano alla versione registrata (`plan_sha`), se la testa lo contiene
        nella storia; `None` altrimenti."""
        i = self.inputs
        sha = i.block.get("plan_sha") if i.block else None
        if not isinstance(sha, str) or not sha:
            return None
        if not git.object_in_history(i.repo, sha, i.head_sha):
            return None
        return git.blob_text(i.repo, sha)

    @cached_property
    def plan_check(self) -> planmod.PlanCheck | None:
        text = self.registered_plan
        if text is None:
            return None
        cfg = self.cfg
        return planmod.check_plan(
            text, required_sections=cfg.get("plan.required_sections"),
            max_scope_files=cfg.get("plan.max_scope_files"),
            must_have_tests=self.components.get("must_have_tests", True), level=self.level,
            profiles=cfg.profiles, active_always=cfg.get("profiles.active"))

    def approved(self, object_: str) -> bool:
        """Un atto `approve <object_>` nel blocco dichiarato, in qualunque stato."""
        acts = self.inputs.block.get("acts") if self.inputs.block else None
        return any(isinstance(a, dict) and a.get("type") == "approve"
                   and a.get("object") == object_ for a in acts or [])


def _red(ev: Evaluation, key: str, family: str, text: str, data: str = "") -> None:
    ev.red.append(Item(key, family, text, data))


def _attention(ev: Evaluation, key: str, family: str, text: str, data: str = "") -> None:
    ev.attention.append(Item(key, family, text, data))


def components_off(ctx: Context, ev: Evaluation) -> None:
    """Ogni componente spento nella configurazione del predefinito (decisione 23)."""
    off = [k for k, v in ctx.components.items() if v is False]
    if off:
        _attention(ev, "components_off", "components",
                   "componenti spenti sul ramo predefinito: " + ", ".join(off))


# --- comandi -------------------------------------------------------------------------------

def _command_state(spec: runner.CommandSpec, r: CommandResult, allow_no_tests: bool) -> str:
    """Lo stato dichiarato e quello ricalcolato da uscita e JUnit: vale il peggiore (un `|| true`
    con un fallito nel report è rosso, 8.1)."""
    if r.state == "unverified":
        return "unverified"
    recomputed = runner.receipt_state(
        exit_code=-1 if r.exit is None else r.exit, report_configured=bool(spec.report),
        junit=r.junit, allow_no_tests=allow_no_tests)
    stated = r.state if r.state in _RANK else "red"
    return max(stated, recomputed, key=_RANK.__getitem__)


def commands(ctx: Context, ev: Evaluation) -> None:
    """Spec 8.1 e 9.2: ogni comando richiesto ha un risultato verde; `empty` e `uncounted` solo
    con `allow_no_tests`, `unverified` solo con `approve unverified-tests` dichiarato. Un
    `setup` rosso (decisione 5) vale come comando rosso."""
    if ctx.inputs.commands is None:
        if ctx.is_github:
            ev.errors.append("risultati dei comandi del gate assenti")
        return
    allow = bool(ctx.cfg.get("project.allow_no_tests"))
    for name, r in ctx.results.items():
        if (name == "setup" or name.endswith(":setup")) and r.state == "red":
            _red(ev, "command_red", "commands", f"il comando «{name}» è rosso")
    counted = False
    for spec in ctx.required:
        r = ctx.results.get(spec.name)
        if r is None:
            _red(ev, "command_missing", "commands",
                 f"il comando «{spec.name}» manca: nessun risultato per la testa")
            continue
        state = _command_state(spec, r, allow)
        if state == "green":
            continue
        if state == "unverified":
            if ctx.approved("unverified-tests"):
                _attention(ev, "unverified_tests", "commands",
                           f"il comando «{spec.name}» non è configurato: approvato "
                           f"`approve unverified-tests`")
            else:
                _red(ev, "command_unverified", "commands",
                     f"il comando «{spec.name}» non è configurato (unverified): serve "
                     f"`approve unverified-tests`")
        elif state == "red":
            detail = f" (uscita {r.exit})" if r.exit not in (None, 0) else ""
            if r.junit is not None and r.junit.failed:
                detail += f", {r.junit.failed} test falliti nel report"
            _red(ev, "command_red", "commands", f"il comando «{spec.name}» è rosso{detail}")
        elif runner.counts_green(state, 0, allow):
            counted = True
            _attention(ev, "no_tests_counted", "commands",
                       f"il comando «{spec.name}» ({state}) vale verde solo per allow_no_tests")
        elif state == "empty":
            _red(ev, "command_empty", "commands",
                 f"il comando «{spec.name}» non ha eseguito nessun test")
        else:
            _red(ev, "command_uncounted", "commands",
                 f"il comando «{spec.name}» non ha un report: i test non sono contati")
    if allow and not counted:
        _attention(ev, "allow_no_tests", "commands", "allow_no_tests è acceso")


# --- identificativi della base --------------------------------------------------------------

def base_path(test_id: str) -> str:
    """Il file di un identificativo `classname::name`: il `classname` se contiene `/`; altrimenti
    il modulo con i punti, come percorso `.py` (senza le classi in coda: i segmenti che
    cominciano con una maiuscola, come `tests.test_x.TestFoo`)."""
    classname = test_id.partition("::")[0]
    if "/" in classname:
        return classname
    parts = classname.split(".")
    while len(parts) > 1 and parts[-1][:1].isupper():
        parts.pop()
    return "/".join(parts) + ".py"


def base_ids(ctx: Context, ev: Evaluation) -> None:
    """Gli identificativi della base, per comando (decisione 12, criteri 10 e 32): ogni test
    eseguito e non saltato nella base deve esserlo anche nella testa, salvo deroghe `test` che
    li elencano tutti. Solo su GitHub e con il componente `base_test_ids` acceso."""
    i = ctx.inputs
    if not ctx.is_github or not ctx.components.get("base_test_ids", True):
        return
    if i.base_ids is None:
        ev.errors.append("identificativi della base non disponibili")
        return
    if i.commands is None:
        return      # l'errore lo dà `commands`
    if i.base_ids_source == BASE_FROM_RUN:
        _attention(ev, "base_ids_from_run", "base_ids",
                   "gli identificativi della base vengono da un run della PR, non dalla cache")
    missing_by_path: dict[str, set[str]] = {}
    failing: set[str] = set()
    for spec in ctx.required:
        r = ctx.results.get(spec.name)
        if r is None or r.junit is None:
            continue
        base = set(i.base_ids.get(spec.name, ()))
        executed = runner.executed_ids(r.junit)
        for tid in base - executed:
            missing_by_path.setdefault(base_path(tid), set()).add(tid)
        failing |= base & set(r.junit.ids_failed)
    found = [Violation("base_id_missing", path, "test della base mancanti nella testa", "test",
                       tuple(sorted(ids)))
             for path, ids in sorted(missing_by_path.items())]
    for v in waivers.unresolved(found, ctx.waiver_file):
        _red(ev, "base_id_missing", "base_ids",
             f"{len(v.ids)} test della base non sono eseguiti nella testa (uno saltato conta "
             f"come mancante)", f"{v.path}: " + ", ".join(v.ids))
    if failing:
        _attention(ev, "base_failing_on_head", "base_ids",
                   f"{len(failing)} test della base falliscono sulla testa",
                   ", ".join(sorted(failing)))


# --- diff: test-guard, scope, piano ---------------------------------------------------------

def _plan_diff(registered: str, head: str) -> str:
    lines = list(difflib.unified_diff(registered.splitlines(), head.splitlines(),
                                      "registrato", "testa", lineterm=""))
    if len(lines) > MAX_PLAN_DIFF_LINES:
        lines = lines[:MAX_PLAN_DIFF_LINES] + ["…"]
    return "\n".join(lines)


def _over_l0(ctx: Context) -> bool:
    """Il diff supera le soglie di L0 (file, righe, byte) o tocca un percorso sensibile."""
    i, cfg = ctx.inputs, ctx.cfg
    lv = cfg.get("levels")
    size = git.diff_size(i.repo, i.base_sha, head=i.head_sha, exclude=output_excludes(cfg))
    computed = levelmod.diff_level(
        [levelmod.FileChange(c.path, c.added, c.removed, c.binary, c.status, c.old_path)
         for c in ctx.changes],
        diff_bytes=size, sensitive_paths=lv["sensitive_paths"], l0_max_files=lv["l0_max_files"],
        l0_max_lines=lv["l0_max_lines"], l0_max_bytes=lv["l0_max_bytes"])
    return computed != "L0"


def _scope(ctx: Context, ev: Evaluation) -> tuple[set[str] | None, set[str], tuple | None,
                                                  tuple | None]:
    """`(scope, locked, registered_plan, approved_spec)` per `diffcheck`. Solo la PR di un lavoro
    con un blocco ha uno scope: quello del piano alla versione registrata (decisione 9)."""
    i, block = ctx.inputs, ctx.inputs.block
    if not ctx.is_work or block is None:
        return None, set(), None, None
    plan_sha, plan_path = block.get("plan_sha"), block.get("plan")
    registered = (plan_path, plan_sha) if isinstance(plan_path, str) and plan_path \
        and ctx.registered_plan is not None else None
    if ctx.level == "L0":
        if not plan_sha and _over_l0(ctx):
            _red(ev, "plan_absent", "diff",
                 "nessun piano registrato e il diff supera le soglie di L0")
        return None, set(), registered, None
    if not plan_sha:
        _red(ev, "plan_sha_absent", "diff", "il blocco non dichiara il piano registrato (plan_sha)")
        return None, set(), None, None
    if ctx.plan_check is None:
        _red(ev, "plan_sha_absent", "diff",
             "il piano registrato (plan_sha) non è nella storia della testa")
        return None, set(), None, None
    locked = {plan_path} if registered else set()
    approved = None
    spec_path = block.get("spec")
    if isinstance(spec_path, str) and spec_path and ctx.issue_no is not None:
        found = l2tree.locate(i.repo, i.head_sha, issue=ctx.issue_no, spec_path=spec_path,
                              spec_blob=None)
        if found is not None:
            locked.add(spec_path)
            approved = (spec_path, found[1]["sha"])
    return set(ctx.plan_check.scope), locked, registered, approved


def _plan_changed(ctx: Context, ev: Evaluation, registered: tuple | None) -> None:
    """Il piano in testa è diverso da quello registrato (criterio 36): `attenzione` con il diff.
    I file che il piano nuovo aggiunge sono fuori scope, perché lo scope resta quello registrato."""
    if registered is None or ctx.registered_plan is None:
        return
    path, sha = registered
    i = ctx.inputs
    if git.blob_at(i.repo, i.head_sha, path) == sha:
        return
    head_text = git.text_at(i.repo, i.head_sha, path) or ""
    _attention(ev, "plan_changed", "diff",
               "il piano in testa è diverso da quello registrato", _plan_diff(ctx.registered_plan,
                                                                               head_text))


def _waiver_items(ctx: Context, ev: Evaluation) -> None:
    """Le deroghe in vigore nel file dell'issue, anche quelle già nella base (8.3, criterio 44)."""
    wf = ctx.waiver_file
    if wf is None:
        return
    sensitive_paths = ctx.cfg.get("levels.sensitive_paths")
    scope_seen = 0
    for w in wf.waivers:
        what = f"deroga {w.id} ({w.type})"
        data = f"{w.file if w.pattern is None else w.pattern}\n{w.choice}\n{w.why}\n{w.cost}"
        if w.pattern is not None:
            _attention(ev, "waiver_pattern", "diff", f"{what} per pattern", data)
        elif w.type == "scope":
            scope_seen += 1
            if scope_seen > waivers.IMMEDIATE_SCOPE or globs.match_any(sensitive_paths, w.file):
                _attention(ev, "waiver_scope_over_two", "diff",
                           f"{what} oltre la seconda o su un file sensibile", data)
            else:
                _attention(ev, "waiver_scope", "diff", what, data)
        else:
            _attention(ev, _WAIVER_KEYS[w.type], "diff", what, data)


def diff(ctx: Context, ev: Evaluation) -> None:
    """test-guard su ogni PR; scope e piano solo per le PR dei lavori (spec 9.2). Le deroghe
    valide sciolgono le violazioni, con le stesse regole di `finish check` in locale: l'unica
    differenza voluta è il piano cambiato dopo la registrazione, che qui è `plan_changed`."""
    i = ctx.inputs
    scope, locked, registered, approved = _scope(ctx, ev)
    check = diffcheck.diff_check(
        ctx.cfg, repo=i.repo, issue=ctx.issue_no or 0, level=ctx.level, base_ref=i.base_sha,
        head_ref=i.head_sha, changes=ctx.changes, scope=scope, locked=locked,
        registered_plan=registered, approved_spec=approved, waiver_file=ctx.waiver_file,
        components=ctx.components, plan_change_is_attention=True)
    for v in check.violations:
        _red(ev, v.kind, "diff", f"{v.detail} ({v.waiver_type})", v.path)
    ev.watch = list(check.watched)
    _plan_changed(ctx, ev, registered)
    _waiver_items(ctx, ev)


# --- must-have ------------------------------------------------------------------------------

def must_have(ctx: Context, ev: Evaluation) -> None:
    """I must-have del piano registrato, ricalcolati dal JUnit della testa (spec 8.7, criterio
    42). Solo per le PR dei lavori in L1 e L2, con il componente `must_have_tests` acceso."""
    if not ctx.components.get("must_have_tests", True) or not ctx.is_work \
            or ctx.level == "L0" or ctx.plan_check is None or ctx.inputs.commands is None:
        return
    ids_run: set[str] = set()
    ids_failed: set[str] = set()
    for r in ctx.results.values():
        if r.junit is not None:
            ids_run.update(r.junit.ids_run)
            ids_failed.update(r.junit.ids_failed)
    res = mustcheck.check(ctx.plan_check.must_haves, ids_run | ids_failed, ids_failed)
    if res.missing:
        _red(ev, "must_have_missing", "must_have",
             f"{len(res.missing)} test dei must-have non sono nel report della testa",
             "; ".join(res.missing))
    if res.failed:
        _red(ev, "must_have_failed", "must_have",
             f"{len(res.failed)} test dei must-have falliscono nella testa", "; ".join(res.failed))
    if res.manual:
        _attention(ev, "manual_must_have", "must_have",
                   "must-have con test manuale: " + ", ".join(res.manual))


FAMILIES = (components_off, commands, base_ids, diff, must_have)


def evaluate(inputs: GateInputs) -> Evaluation:
    """Il giudizio sul gate: voci rosse, voci di `attenzione`, file osservati ed errori. Un
    errore di git o di lettura è un `error` con il motivo, mai un traceback."""
    ev = Evaluation()
    ctx = Context(inputs)
    for family in FAMILIES:
        try:
            family(ctx, ev)
        except git.GitError as e:
            ev.errors.append(f"{family.__name__}: {e}")
    return ev
