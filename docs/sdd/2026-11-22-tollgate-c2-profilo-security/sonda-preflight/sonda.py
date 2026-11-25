#!/usr/bin/env python3
"""Sonda dello scan pre-flight di C2: la tabella delle precedenze della decisione 5, caso per caso.

Uso (mai dal repo vivo: `rilancia.sh` fa la copia `git archive` e chiama questo file):

    python3 -B sonda.py --codice <copia con bin/ e templates/> [--frammento <security.toml>]

Se `bin/tollgate_core/fragments.py` della copia non conosce ancora `keep_paths`, la sonda la
simula su una copia privata (cartella temporanea `tollgate-sonda-…`): `[detect] keep_paths` letto
da `_parse` e la condizione di `lighting` che diventa `f in mine or f not in taken or
fragment.keep_paths`. Se la copia non ha `templates/profiles/security.toml`, usa il frammento
candidato accanto a questo file. Non tocca rete, stato di tollgate né il repo.
Uscita: una riga per caso (`uguale` / `DIVERSO` con la differenza esatta) e l'esito in fondo;
codice d'uscita 0 solo se tutti i casi della tabella sono uguali.
"""
from __future__ import annotations

import argparse
import shutil
import sys
import tempfile
import tomllib
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent

B, F, A, D, I, S = "backend", "frontend", "ai", "database", "infra", "security"

# (caso, file, detected, proposta come scritta, runtime come scritto, profili che devono essere attivi)
CASES = [
 ("S1", ["src/auth/login.ts"], {}, {S: ["src/auth/**"]}, {"src/auth/login.ts": S}, {}),
 ("S2", ["server/app.py", "server/auth/jwt.py"], {}, {B: ["/server/**"], S: ["server/auth/**"]},
  {"server/app.py": B, "server/auth/jwt.py": S}, {}),
 ("S3", ["api/users.ts", "api/auth/login.ts"], {}, {B: ["/api/**"], S: ["api/auth/**"]},
  {"api/users.ts": B, "api/auth/login.ts": S}, {}),
 ("S4", ["src/components/Button.tsx", "src/components/auth/LoginForm.tsx"], {},
  {F: ["src/components/**"], S: ["src/components/auth/**"]},
  {"src/components/auth/LoginForm.tsx": S}, {"src/components/auth/LoginForm.tsx": [F, S]}),
 ("S5", ["app/page.tsx", "app/auth/callback/route.ts"], {}, {F: ["**/*.tsx"], S: ["app/auth/**"]},
  {"app/auth/callback/route.ts": S}, {}),
 ("S6", ["app/(auth)/login/page.tsx"], {}, {F: ["**/*.tsx"]}, {"app/(auth)/login/page.tsx": F}, {}),
 ("S7", ["middleware.ts", "app/page.tsx"], {}, {F: ["**/*.tsx"], S: ["/middleware.ts"]},
  {"middleware.ts": S}, {}),
 ("S8", ["src/middleware.ts", "src/main.ts"], {}, {S: ["src/middleware.ts"]}, {"src/main.ts": None}, {}),
 ("S9", ["server/app.ts", "server/middleware.ts"], {}, {B: ["/server/**"], S: ["server/middleware.ts"]},
  {"server/middleware.ts": S}, {}),
 ("S10", ["src/lib/supabase/middleware.ts", "src/lib/supabase/client.ts"], {},
  {S: ["src/lib/supabase/middleware.ts"]}, {"src/lib/supabase/client.ts": None}, {}),
 ("S11", ["supabase/functions/auth/index.ts", "supabase/migrations/1.sql"], {}, {D: ["/supabase/**"]},
  {"supabase/functions/auth/index.ts": D, "supabase/migrations/1.sql": D}, {}),
 ("S12", ["supabase/rls/policies.sql", "supabase/config.toml"], {}, {D: ["/supabase/**"]},
  {"supabase/rls/policies.sql": D, "supabase/config.toml": D}, {}),
 ("S13", ["db/rls/policies.sql", "db/schema.sql"], {}, {D: ["**/*.sql"], S: ["db/rls/**"]},
  {"db/rls/policies.sql": S, "db/schema.sql": D}, {"db/rls/policies.sql": [D, S]}),
 ("S14", ["src/auth/llm/client.py", "src/auth/login.py"], {}, {A: ["src/auth/llm/**"], S: ["src/auth/**"]},
  {"src/auth/llm/client.py": A}, {}),
 ("S15", ["src/ai/auth/key.py", "src/ai/agent.py"], {}, {A: ["src/ai/**"], S: ["src/ai/auth/**"]},
  {"src/ai/auth/key.py": S}, {}),
 ("S16", ["src/auth/components/Login.tsx", "src/auth/session.ts"], {},
  {F: ["src/auth/components/**"], S: ["src/auth/**"]}, {"src/auth/components/Login.tsx": F},
  {"src/auth/components/Login.tsx": [F, S]}),
 ("S17", ["server/routes/auth/login.ts", "server/app.ts"], {},
  {B: ["/server/**"], S: ["server/routes/auth/**"]}, {"server/routes/auth/login.ts": S}, {}),
 ("S18", ["src/routes/auth/login.ts", "src/routes/users.ts"], {},
  {B: ["src/routes/**"], S: ["src/routes/auth/**"]}, {"src/routes/auth/login.ts": S}, {}),
 ("S19", ["infra/auth/policy.json", "infra/main.ts"], {}, {I: ["/infra/**"], S: ["infra/auth/**"]},
  {"infra/auth/policy.json": S}, {}),
 ("S20", ["src/auth/Dockerfile", "src/auth/main.go"], {}, {I: ["src/auth/Dockerfile"], S: ["src/auth/**"]},
  {"src/auth/Dockerfile": I}, {}),
 ("S21", ["src/auth/schema.sql", "src/auth/migrations/1.sql"], {},
  {D: ["**/*.sql", "src/auth/migrations/**"], S: ["src/auth/**"]},
  {"src/auth/schema.sql": S, "src/auth/migrations/1.sql": D}, {}),
 ("S22", ["tests/auth/test_login.py", "app/main.py"], {}, {S: ["tests/auth/**"]},
  {"tests/auth/test_login.py": S}, {}),
 ("S23", ["docs/security/policy.md", "SECURITY.md"], {}, {},
  {"docs/security/policy.md": None, "SECURITY.md": None}, {}),
 ("S24", ["docs/security/policy.md", "docs/security/check.py"], {}, {S: ["docs/security/**"]},
  {"docs/security/policy.md": S, "docs/security/check.py": S}, {}),
 ("S25", [".github/tollgate/bin/auth/x.py", ".github/workflows/security/a.yml", ".claude/auth/x.md",
          "src/main.py"], {}, {},
  {".github/tollgate/bin/auth/x.py": None, ".github/workflows/security/a.yml": None,
   ".claude/auth/x.md": None, "src/main.py": None}, {}),
 ("S26", ["src/lib/jwt.ts", "src/lib/date.ts"], {S: ["src/lib/jwt.ts"]}, {S: ["src/lib/jwt.ts"]},
  {"src/lib/date.ts": None}, {}),
 ("S27", ["api/login.ts", "api/users.ts"], {S: ["api/login.ts"]}, {B: ["/api/**"], S: ["api/login.ts"]},
  {"api/login.ts": S}, {}),
 ("S28", ["api/login.ts"], {S: ["api/login.ts"], B: ["api/login.ts"]},
  {B: ["/api/**"], S: ["api/login.ts"]}, {"api/login.ts": S}, {}),
 ("S29", ["src/lib/auth-client.ts"], {A: ["src/lib/auth-client.ts"], S: ["src/lib/auth-client.ts"]},
  {A: ["src/lib/auth-client.ts"], S: ["src/lib/auth-client.ts"]}, {"src/lib/auth-client.ts": A}, {}),
 ("S30", ["web/auth/login.tsx", "web/index.html"], {}, {F: ["/web/**"], S: ["web/auth/**"]},
  {"web/auth/login.tsx": S}, {}),
 ("S31", ["src/security/csp.ts", "src/security/headers.ts"], {}, {S: ["src/security/**"]},
  {"src/security/csp.ts": S, "src/security/headers.ts": S}, {}),
 ("S32", ["src/session.ts", "src/agents/session.py"], {}, {A: ["src/agents/**"]},
  {"src/session.ts": None, "src/agents/session.py": A}, {}),
 ("S33", ["functions/auth/index.js", "functions/api.js"], {}, {B: ["/functions/**"], S: ["functions/auth/**"]},
  {"functions/auth/index.js": S}, {}),
 ("S34", ["prisma/auth/schema.prisma", "prisma/schema.prisma"], {}, {D: ["/prisma/**"], S: ["prisma/auth/**"]},
  {"prisma/auth/schema.prisma": S}, {}),
 ("S35", ["src/auth/middleware.ts", "src/auth/jwt.ts"], {}, {S: ["src/auth/**"]},
  {"src/auth/middleware.ts": S, "src/auth/jwt.ts": S}, {}),
 ("S36", ["middleware.py", "app/views.py"], {}, {S: ["/middleware.py"]}, {"app/views.py": None}, {}),
 ("S37", ["supabase/functions/x/index.ts"], {}, {D: ["/supabase/**"]},
  {"supabase/functions/x/index.ts": D}, {}),
 ("S38", ["src/auth/README.md", "src/auth/guida.md"], {}, {},
  {"src/auth/README.md": None, "src/auth/guida.md": None}, {}),
 ("S39", ["src/components/auth/Login.tsx", "src/components/auth/login.css", "src/components/Nav.tsx"], {},
  {F: ["src/components/**"], S: ["src/components/auth/**"]},
  {"src/components/auth/login.css": S, "src/components/Nav.tsx": F}, {}),
 ("S40", ["src/prompts/auth/system.md", "src/prompts/auth/build.ts"], {},
  {A: ["src/prompts/**"], S: ["src/prompts/auth/**"]},
  {"src/prompts/auth/system.md": S, "src/prompts/auth/build.ts": S}, {}),
 ("S41", ["server/auth.ts", "server/app.ts"], {S: ["server/auth.ts"]},
  {B: ["/server/**"], S: ["server/auth.ts"]}, {"server/auth.ts": S}, {}),
 ("S42", ["src/auth/index.ts", "src/auth/jwt.ts"], {A: ["src/auth/index.ts"]},
  {A: ["src/auth/index.ts"], S: ["src/auth/**"]}, {"src/auth/index.ts": A}, {}),
 ("S43", ["supabase/functions/login/index.ts", "supabase/config.toml"],
  {S: ["supabase/functions/login/index.ts"]}, {D: ["/supabase/**"]},
  {"supabase/functions/login/index.ts": D, "supabase/config.toml": D}, {}),
 ("S44", [".github/workflows/security.yml", ".github/security/policy.yml", "src/a.py"], {},
  {S: [".github/security/**"]}, {".github/security/policy.yml": S}, {}),
 ("S45", ["proxy.ts", "app/page.tsx"], {}, {F: ["**/*.tsx"], S: ["/proxy.ts"]}, {"proxy.ts": S}, {}),
 ("S46", ["src/utils/proxy.ts", "vite.config.ts"], {}, {S: ["src/utils/proxy.ts"]},
  {"src/utils/proxy.ts": S}, {}),
 ("S47", ["src/proxy.js", "server/proxy.js", "server/app.js"], {},
  {B: ["/server/**"], S: ["server/proxy.js", "src/proxy.js"]}, {"server/proxy.js": S}, {}),
 ("S48", ["proxy.py", "src/proxy.tsx"], {}, {F: ["**/*.tsx"]}, {"proxy.py": None, "src/proxy.tsx": F}, {}),
 ("S49", ["src/app/api/auth/x/route.ts", "src/app/page.tsx"], {B: ["src/app/api/auth/x/route.ts"]},
  {B: ["src/app/api/auth/x/route.ts"], F: ["**/*.tsx"], S: ["src/app/api/auth/**"]},
  {"src/app/api/auth/x/route.ts": B}, {"src/app/api/auth/x/route.ts": [B, S]}),
 ("S50", ["app/auth/callback/route.ts", "app/auth/actions.ts", "app/page.tsx"],
  {B: ["app/auth/callback/route.ts"]},
  {B: ["app/auth/callback/route.ts"], F: ["**/*.tsx"], S: ["app/auth/**"]},
  {"app/auth/callback/route.ts": B, "app/auth/actions.ts": S}, {"app/auth/callback/route.ts": [B, S]}),
 ("S51", ["src/auth/routes/login.ts", "src/auth/jwt.ts"], {},
  {B: ["src/auth/routes/**"], S: ["src/auth/**"]}, {"src/auth/routes/login.ts": B}, {}),
 ("S52", ["src/auth/handlers/login.ts", "src/auth/jwt.ts"], {},
  {B: ["src/auth/handlers/**"], S: ["src/auth/**"]}, {"src/auth/handlers/login.ts": B}, {}),
 ("S53", ["server/auth/login.ts", "server/auth/router.ts", "server/app.ts"],
  {B: ["server/auth/login.ts", "server/auth/router.ts", "server/app.ts"]},
  {B: ["/server/**"], S: ["server/auth/**"]},
  {"server/auth/login.ts": S, "server/auth/router.ts": S, "server/app.ts": B}, {}),
 ("S54", ["src/components/auth/Login.tsx", "src/components/A.tsx"], {F: ["src/components/auth/Login.tsx"]},
  {F: ["src/components/**"], S: ["src/components/auth/**"]}, {"src/components/auth/Login.tsx": S}, {}),
 ("S55", ["src/login.ts"], {B: ["src/login.ts"], S: ["src/login.ts"]},
  {B: ["src/login.ts"], S: ["src/login.ts"]}, {"src/login.ts": B}, {}),
 ("S56", ["apps/web/supabase/functions/auth/index.ts", "apps/web/supabase/migrations/1.sql"], {},
  {D: ["apps/web/supabase/migrations/**"], S: ["apps/web/supabase/functions/auth/**"]},
  {"apps/web/supabase/functions/auth/index.ts": S}, {}),
 ("S57", ["infra/middleware.ts", "infra/main.tf"], {}, {I: ["/infra/**"], S: ["infra/middleware.ts"]},
  {"infra/middleware.ts": S}, {}),
 ("S58", ["src/auth/Guard.ts", "src/auth/x.ts"], {F: ["src/auth/Guard.ts"]},
  {F: ["src/auth/Guard.ts"], S: ["src/auth/**"]}, {"src/auth/Guard.ts": F}, {}),
 ("S59", ["src/middleware.test.ts", "middleware.config.json", "docs/middleware.md"], {},
  {S: ["/middleware.config.json", "src/middleware.test.ts"]},
  {"src/middleware.test.ts": S, "middleware.config.json": S, "docs/middleware.md": None}, {}),
 ("S60", ["src/Auth/Login.cs", "functions/_middleware.ts", "functions/api.ts"], {}, {B: ["/functions/**"]},
  {"src/Auth/Login.cs": None, "functions/_middleware.ts": B}, {}),
 ("S61", ["server/middleware.ts", "server/app.ts"], {B: ["server/middleware.ts", "server/app.ts"]},
  {B: ["/server/**"], S: ["server/middleware.ts"]}, {"server/middleware.ts": S}, {}),
 ("S62", ["src/middleware.ts", "src/main.ts"], {B: ["src/middleware.ts"]},
  {B: ["src/middleware.ts"], S: ["src/middleware.ts"]}, {"src/middleware.ts": B},
  {"src/middleware.ts": [B, S]}),
 ("S63", ["src/middleware.ts", "src/x.ts"], {A: ["src/middleware.ts"]},
  {A: ["src/middleware.ts"], S: ["src/middleware.ts"]}, {"src/middleware.ts": A},
  {"src/middleware.ts": [A, S]}),
 ("S64", ["proxy.ts", "app/page.tsx"], {B: ["proxy.ts"]},
  {B: ["/proxy.ts"], F: ["**/*.tsx"], S: ["/proxy.ts"]}, {"proxy.ts": B}, {"proxy.ts": [B, S]}),
 ("S65", ["src/auth/schema.ts", "src/auth/x.ts"], {D: ["src/auth/schema.ts"]},
  {D: ["src/auth/schema.ts"], S: ["src/auth/**"]}, {"src/auth/schema.ts": D, "src/auth/x.ts": S}, {}),
 ("S66", ["src/middleware.d.ts", "src/Middleware.ts", "src/middlewarex.ts"], {},
  {S: ["src/middleware.d.ts"]},
  {"src/middleware.d.ts": S, "src/Middleware.ts": None, "src/middlewarex.ts": None}, {}),
 ("S68", ["db/migrations/auth/001.sql", "db/migrations/002.sql"], {},
  {D: ["db/migrations/**"], S: ["db/migrations/auth/**"]}, {"db/migrations/auth/001.sql": S},
  {"db/migrations/auth/001.sql": [D, S]}),
 ("S69", ["infra/security/sg.tf", "infra/main.tf"], {}, {I: ["/infra/**"], S: ["infra/security/**"]},
  {"infra/security/sg.tf": S}, {}),
 ("S70", ["packages/auth/package.json", "packages/auth/src/index.ts", "packages/web/x.ts"], {},
  {S: ["packages/auth/**"]},
  {"packages/auth/package.json": S, "packages/auth/src/index.ts": S}, {}),
 ("S71", ["src/ai/middleware.ts", "src/ai/agent.py"], {}, {A: ["src/ai/**"], S: ["src/ai/middleware.ts"]},
  {"src/ai/middleware.ts": S}, {}),
]

# Casi che la tabella non ha: attese scritte dallo scan (colonna «attesa dello scan»), non dal piano.
EXTRA = [
 ("N1 edge function sotto supabase/ alla radice trovata da ai: l'exclude batte keep_paths",
  ["supabase/functions/auth/index.ts", "supabase/config.toml"], {A: ["supabase/functions/auth/index.ts"]},
  {A: ["supabase/functions/auth/index.ts"], D: ["/supabase/**"]},
  {"supabase/functions/auth/index.ts": A}, {}),
 ("N2 file sotto server/auth/ trovato da backend E da security",
  ["server/auth/login.ts", "server/app.ts"], {B: ["server/auth/login.ts"], S: ["server/auth/login.ts"]},
  {B: ["/server/**"], S: ["server/auth/**"]}, {"server/auth/login.ts": S, "server/app.ts": B}, {}),
 ("N3 cartelle middleware/ e middlewares/ (decisione 1: fuori)",
  ["src/middleware/auth.ts", "src/middlewares/cors.ts"], {}, {},
  {"src/middleware/auth.ts": None, "src/middlewares/cors.ts": None}, {}),
 ("N4 .tsx dentro auth/ senza cartella di frontend: l'estensione perde",
  ["src/auth/Login.tsx", "src/Home.tsx"], {}, {F: ["**/*.tsx"], S: ["src/auth/**"]},
  {"src/auth/Login.tsx": S, "src/Home.tsx": F}, {"src/auth/Login.tsx": [F, S]}),
 ("N5 src/auth/middleware.ts trovato da backend: percorso esatto di backend, security attivo",
  ["src/auth/middleware.ts", "src/auth/jwt.ts"], {B: ["src/auth/middleware.ts"]},
  {B: ["src/auth/middleware.ts"], S: ["src/auth/**"]},
  {"src/auth/middleware.ts": B, "src/auth/jwt.ts": S}, {"src/auth/middleware.ts": [B, S]}),
 ("N6 src/middleware.ts trovato da frontend: parità, ordine alfabetico",
  ["src/middleware.ts", "src/main.ts"], {F: ["src/middleware.ts"]},
  {F: ["src/middleware.ts"], S: ["src/middleware.ts"]}, {"src/middleware.ts": F},
  {"src/middleware.ts": [F, S]}),
 ("N7 supabase/middleware.ts alla radice: escluso anche per nome",
  ["supabase/middleware.ts", "supabase/config.toml"], {}, {D: ["/supabase/**"]},
  {"supabase/middleware.ts": D}, {}),
 ("N8 security/ che contiene auth/: vince la cartella più a sinistra",
  ["security/auth/x.py", "security/y.py"], {}, {S: ["/security/**"]},
  {"security/auth/x.py": S, "security/y.py": S}, {}),
 ("N9 test con un marcatore dentro una cartella auth/ con accanto un sorgente trovato da backend",
  ["src/auth/login.test.ts", "src/auth/login.ts"], {B: ["src/auth/login.ts"]},
  {B: ["src/auth/login.ts"], S: ["src/auth/**"]},
  {"src/auth/login.ts": B, "src/auth/login.test.ts": S}, {}),
 ("N10 vendor/…/auth/ (costo della decisione 1): codice di terzi a security",
  ["vendor/lib/auth/a.go", "main.go"], {}, {S: ["vendor/lib/auth/**"]}, {"vendor/lib/auth/a.go": S}, {}),
 ("N11 middleware.yaml e proxy.json: il primo accende, il secondo no",
  ["deploy/middleware.yaml", "proxy.json"], {}, {S: ["deploy/middleware.yaml"]},
  {"deploy/middleware.yaml": S, "proxy.json": None}, {}),
 ("N12 auth/ alla radice con routes/ dentro",
  ["auth/login.py", "auth/routes/api.py"], {}, {B: ["auth/routes/**"], S: ["/auth/**"]},
  {"auth/login.py": S, "auth/routes/api.py": B}, {"auth/routes/api.py": [B, S]}),
]


def simulate(private: Path) -> bool:
    """Aggiunge `keep_paths` al codice della copia privata se manca. Vero se ha simulato."""
    frag = private / "bin" / "tollgate_core" / "fragments.py"
    text = frag.read_text(encoding="utf-8")
    if "keep_paths" in text:
        return False
    edits = [
        ('    exclude: tuple[str, ...] = ()\n',
         '    exclude: tuple[str, ...] = ()\n    keep_paths: bool = False\n'),
        ('{"content", "exclude"}', '{"content", "exclude", "keep_paths"}'),
        ('                    tuple(exclude))', '                    tuple(exclude), detect.get("keep_paths", False) is True)'),
    ]
    for old, new in edits:
        assert text.count(old) == 1, f"fragments.py: «{old.strip()}» non trovato una volta sola"
        text = text.replace(old, new)
    frag.write_text(text, encoding="utf-8")
    ini = private / "bin" / "tollgate_flow" / "init.py"
    text = ini.read_text(encoding="utf-8")
    old = "and (f in mine or f not in taken)]"
    assert text.count(old) == 1, "init.py: la condizione di lighting non è quella attesa"
    ini.write_text(text.replace(old, "and (f in mine or f not in taken or fragment.keep_paths)]"),
                   encoding="utf-8")
    return True


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--codice", required=True, help="copia del repo (git archive) con bin/ e templates/")
    ap.add_argument("--frammento", default=str(HERE / "security.toml"),
                    help="frammento security da usare se la copia non ne ha uno")
    args = ap.parse_args()
    code = Path(args.codice).resolve()
    tmp = tempfile.TemporaryDirectory(prefix="tollgate-sonda-")
    private = Path(tmp.name)
    try:
        shutil.copytree(code / "bin", private / "bin", ignore=shutil.ignore_patterns("__pycache__"))
        shutil.copytree(code / "templates", private / "templates")
        simulated = simulate(private)
        real_fragment = private / "templates" / "profiles" / "security.toml"
        candidate = not real_fragment.exists()
        if candidate:
            shutil.copy(args.frammento, real_fragment)
        sys.path.insert(0, str(private / "bin"))
        from tollgate_analysis import profiles
        from tollgate_core import fragments
        from tollgate_flow import init
        # La radice del plugin della sonda: frammenti veri + security, skill finte approvate, agenti finti.
        root = private / "plugin"
        (root / "templates" / "profiles").mkdir(parents=True)
        (root / "agents").mkdir()
        for fr in fragments.load(private):
            shutil.copy(fr.source, root / "templates" / "profiles" / fr.source.name)
            skill = root / "skills" / f"rules-{fr.area}"
            skill.mkdir(parents=True)
            (skill / "SKILL.md").write_text(
                f"---\napproved: 2026-11-01\n---\nR-{fr.area.upper()}-01 [blocca] x\n", encoding="utf-8")
            for key in ("agent", "reviewer", "final_specialist"):
                if (value := fr.profile.get(key)):
                    (root / "agents" / f"{value.partition(':')[2]}.md").write_text(
                        "---\nname: a\n---\n", encoding="utf-8")
        base = (code / "templates" / "tollgate.toml").read_text(encoding="utf-8")
        base = base.replace("__MODE__", "detect")
        sec = next(f for f in fragments.load(root) if f.area == "security")
        print(f"codice: {code}")
        print(f"keep_paths: {'SIMULATA dalla sonda' if simulated else 'del codice (Task 3)'}; "
              f"frammento security: {'CANDIDATO della sonda' if candidate else 'del repo (Task 4)'}; "
              f"keep_paths del frammento = {getattr(sec, 'keep_paths', None)}")
        print(f"pattern: {[p.kind + ':' + p.name for p in sec.patterns]}; exclude: {list(sec.exclude)}; "
              f"marcatori: {len(sec.detect)}")

        def run(files, detected):
            got = init.profile_blocks({f: 10 for f in files}, base, root, detected=detected or None)
            declared = tomllib.loads(base + got.text).get("profiles", {})
            declared = {k: v for k, v in declared.items() if isinstance(v, dict)}
            proposal = {a: sorted(p["paths"]) for a, p in declared.items()}
            runtime = {f: profiles.vertical_for(f, declared) for f in files}
            active = {f: profiles.active_profiles([f], declared, []) for f in files}
            return proposal, runtime, active, declared

        def report(cases, label):
            same = 0
            different = []
            for name, files, detected, proposal, runtime, active in cases:
                got_p, got_r, got_a, declared = run(files, detected)
                diffs = []
                want_p = {a: sorted(p) for a, p in proposal.items()}
                if got_p != want_p:
                    diffs.append(f"Proposta: attesa {want_p}, ottenuta {got_p}")
                for f, area in runtime.items():
                    if got_r[f] != area:
                        diffs.append(f"Runtime: {f} atteso {area}, ottenuto {got_r[f]}")
                for f, names in active.items():
                    if sorted(got_a[f]) != sorted(names):
                        diffs.append(f"Attivi: {f} attesi {sorted(names)}, ottenuti {sorted(got_a[f])}")
                if "final_specialist" in declared.get("security", {}) or "security" not in declared:
                    pass
                else:
                    diffs.append("security proposto senza final_specialist")
                if diffs:
                    different.append(name.split()[0])
                    print(f"{name}: DIVERSO — " + "; ".join(diffs))
                else:
                    same += 1
                    rest = {f: a for f, a in got_r.items() if f not in runtime}
                    print(f"{name}: uguale — proposta {got_p}; runtime {got_r if not rest else {**{f: got_r[f] for f in runtime}, **rest}}")
            print(f"== {label}: {same} su {len(cases)} uguali" + (f"; diversi: {', '.join(different)}" if different else ""))
            return different

        bad = report(CASES, "tabella della decisione 5 (S1-S66, S68-S71)")
        # S67, solo runtime: due blocchi scritti a mano.
        f67 = "supabase/functions/auth/index.ts"
        hand_a = {"database": {"paths": ["/supabase/**"]}, "security": {"paths": ["**/auth/**"]}}
        hand_b = {"database": {"paths": ["/supabase/**"]}, "security": {"paths": ["supabase/functions/auth/**"]}}
        a = profiles.vertical_for(f67, hand_a)
        a_active = profiles.active_profiles([f67], hand_a, [])
        b = profiles.vertical_for(f67, hand_b)
        ok67 = a == "database" and "security" in a_active and b == "security"
        print(f"S67 (a mano, solo runtime): con **/auth/** → {a} (attivi {a_active}); con "
              f"supabase/functions/auth/** → {b}: {'uguale' if ok67 else 'DIVERSO'}")
        extra_bad = report(EXTRA, "casi che la tabella non ha (attese dello scan)")
        tmp_ok = not bad and ok67
        print(f"ESITO: {len(CASES) - len(bad)} casi su {len(CASES)} uguali alla tabella"
              + (f" (diversi: {', '.join(bad)})" if bad else "")
              + f"; S67 {'uguale' if ok67 else 'DIVERSO'}; casi in più: "
              + (f"{len(EXTRA) - len(extra_bad)} su {len(EXTRA)} come attesi dallo scan"
                 + (f" (diversi: {', '.join(extra_bad)})" if extra_bad else "")))
        return 0 if tmp_ok else 1
    finally:
        tmp.cleanup()


if __name__ == "__main__":
    sys.exit(main())
