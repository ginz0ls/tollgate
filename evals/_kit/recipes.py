"""Ricette del banco degli eval (decisione 3): lo stato di tollgate che lo scaffold costruisce.

Una ricetta descrive, con i soli dati, cosa deve esistere nel workspace quando l'agente parte. La
costruisce `scaffold.build` con il programma vero, mai scrivendo nel DB. Le ricette dei singoli casi
(Task 8-10) compongono queste primitive; ogni primitiva ha il suo `test_build_<ricetta>` in
`tests/test_eval_kit.py`.

Campi di composizione (Task 7): `change` (L0: i file di `fixtures/changes/<change>/` committati dalla
sessione principale), `audit_rounds` (giri di audit di L2 chiusi puliti), `acts` (atti dell'utente
con la sessione `scaffold`, applicati con `act apply`), `finish` (`check` o `open-pr`). Servono a
descrivere la sequenza di eventi e comandi di ogni ricetta senza codice per ricetta."""
from __future__ import annotations

from dataclasses import dataclass, field

LEVELS = ("L0", "L1", "L2")
FINISH_STEPS = ("check", "open-pr")


@dataclass(frozen=True)
class Recipe:
    name: str
    level: str
    issue: int = 1
    issue_title: str = "Aggiungi la moltiplicazione"      # fissa lo slug del ramo e il percorso del worktree
    plan: str | None = None             # nome di un piano in fixtures/plans/ (L1: registrato con Write)
    tasks_done: tuple[int, ...] = ()    # task chiusi (implementatore, ricevuta verify, revisore, task done)
    task_started: int | None = None     # task avviato con `task start` e lasciato running
    spec: str | None = None             # nome di una spec in fixtures/specs/ (L2: scritta e committata)
    phase: str | None = None            # fase attesa alla fine (controllo dello scaffold)
    extra_files: dict[str, str] = field(default_factory=dict)   # file aggiunti al progetto di base (commit `base` su main)
    gh_data: dict = field(default_factory=dict)                 # dati del gh finto, sopra quelli di base
    change: str | None = None           # L0: cartella di fixtures/changes/ da committare
    audit_rounds: int = 0               # L2: giri di audit chiusi puliti
    acts: tuple[tuple[str, ...], ...] = ()   # atti dell'utente: (tipo, argomenti...), poi `act apply`
    finish: str | None = None           # None | "check" | "open-pr"

    def __post_init__(self):
        if self.level not in LEVELS:
            raise ValueError(f"livello sconosciuto: {self.level}")
        if self.finish is not None and self.finish not in FINISH_STEPS:
            raise ValueError(f"finish sconosciuto: {self.finish}")
        if self.level == "L0" and (self.plan or self.spec or self.tasks_done or self.task_started):
            raise ValueError("L0 non ha piano, spec né task")
        if self.level != "L2" and (self.spec or self.audit_rounds):
            raise ValueError("spec e giri di audit sono di L2")
        if self.change and self.level != "L0":
            raise ValueError("`change` è il lavoro della sessione principale, solo in L0")
        if self.finish == "open-pr" and self.level != "L0":
            raise ValueError("`finish open-pr` serve un ciclo di revisione finale in L1 e L2: "
                             "il banco lo costruisce solo in L0")


RECIPES: dict[str, Recipe] = {r.name: r for r in (
    Recipe("l0-execution", "L0", phase="execution"),
    Recipe("l0-review", "L0", change="calc-l0", finish="check", phase="review"),
    Recipe("l0-pr-open", "L0", change="calc-l0", finish="open-pr", phase="pr_open"),
    Recipe("l0-level-cap", "L0", acts=(("approve", "level", "L0", "prova del banco"),),
           phase="execution"),
    Recipe("l1-plan", "L1", phase="plan"),
    Recipe("l1-plan-registered", "L1", plan="calc-l1", phase="execution"),
    Recipe("l1-execution", "L1", plan="calc-l1", task_started=1, phase="execution"),
    Recipe("l1-task-done", "L1", plan="calc-l1", tasks_done=(1,), phase="execution"),
    Recipe("l1-review", "L1", plan="calc-l1", tasks_done=(1, 2), finish="check", phase="review"),
    Recipe("l2-spec-audit", "L2", spec="calc-l2", phase="spec_audit"),
    Recipe("l2-spec-audited", "L2", spec="calc-l2", audit_rounds=1, phase="spec_audit"),
    Recipe("l2-spec-approved", "L2", spec="calc-l2", audit_rounds=1,
           acts=(("approve", "spec", "1"),), phase="plan"),
)}

# Per caso (non per ricetta): i cammini corretti e, per ognuno, i nomi dei grader che passano. Li
# dichiarano i Task 8-10 insieme ai `case.yaml`; `test_correct_paths_score_above_threshold` calcola
# con loro il punteggio contro la soglia (decisione 7).
CORRECT_PATHS: dict[str, tuple[tuple[str, ...], ...]] = {}
