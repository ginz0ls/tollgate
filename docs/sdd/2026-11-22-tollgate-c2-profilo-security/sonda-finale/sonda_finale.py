#!/usr/bin/env python3
"""Sonda della revisione finale di C2: casi di precedenza nuovi (oltre S1-S71 e N1-N12), sui
frammenti, le skill e gli agenti veri di una copia `git archive` del commit. Uso:
    python3 -B sonda_finale.py --codice <copia>
Non tocca rete, stato di tollgate né il repo vivo. Tre parti: (1) casi di proposta e runtime;
(2) `keep_paths` non cambia i blocchi degli altri frammenti (confronto con una copia del
frammento senza la chiave, e con il frammento tolto); (3) rilevamento vero (`git grep`) in un
repo temporaneo."""
from __future__ import annotations
import argparse, shutil, subprocess, sys, tempfile, tomllib, os
from pathlib import Path
sys.dont_write_bytecode = True
B, F, A, D, I, S = "backend", "frontend", "ai", "database", "infra", "security"

# (nome, file, detected) — l'esito si stampa e lo legge il revisore
CASES = [
 ("X1 Dockerfile sotto infra/auth/", ["infra/auth/Dockerfile", "infra/main.tf"], {}),
 ("X2 rls/ alla radice con .sql", ["rls/policies.sql", "schema.sql"], {}),
 ("X3 nomi vicini che non accendono", ["auth.ts", "src/auth.config.ts", "src/authz/x.ts", "src/oauth/cb.ts", "src/authentication/x.ts", "src/security.ts", "src/proxy.mjs", "src/middleware/x.ts"], {}),
 ("X4 auth/ alla radice e supabase/auth/", ["supabase/auth/x.ts", "auth/y.ts", "supabase/config.toml"], {}),
 ("X5 schema drizzle in src/db/auth trovato da database, accanto a migrations", ["src/db/migrations/auth/schema.ts", "src/db/migrations/0001.sql"], {D: ["src/db/migrations/auth/schema.ts"]}),
 ("X6 src/middleware.ts trovato da backend E da security", ["src/middleware.ts", "src/main.ts"], {B: ["src/middleware.ts"], S: ["src/middleware.ts"]}),
 ("X7 supabase/ annidata: edge function di login trovata da security", ["apps/web/supabase/functions/login/index.ts", "apps/web/supabase/config.toml", "apps/web/supabase/migrations/1.sql"], {S: ["apps/web/supabase/functions/login/index.ts"]}),
 ("X8 supabase/ alla radice: file trovato da database E da security", ["supabase/functions/login/index.ts", "supabase/config.toml"], {D: ["supabase/functions/login/index.ts"], S: ["supabase/functions/login/index.ts"]}),
 ("X9 .github/actions/auth e .github/auth", [".github/actions/auth/action.yml", ".github/auth/x.yml", "src/a.py"], {}),
 ("X10 src/auth/proxy.ts trovato da frontend, src/proxy.ts no", ["src/auth/proxy.ts", "src/proxy.ts", "src/auth/x.ts"], {F: ["src/auth/proxy.ts"]}),
 ("X11 e2e/auth con solo test", ["e2e/auth/login.spec.ts", "src/main.ts"], {}),
 ("X12 documenti e proxy.ts sotto docs/", ["middleware.md", "middleware.txt", "docs/proxy.ts", "docs/guida.md"], {}),
 ("X13 tests/middleware.py", ["tests/middleware.py", "app/main.py"], {}),
 ("X14 pacchetto auth con supabase/ dentro", ["packages/auth/supabase/functions/x/index.ts", "packages/auth/supabase/migrations/1.sql", "packages/auth/src/i.ts"], {}),
 ("X15 server/auth/Login.tsx (frontend esclude server/)", ["server/auth/Login.tsx", "server/app.ts", "src/Home.tsx"], {}),
 ("X16 functions/auth/_middleware.ts e functions/auth/middleware.ts", ["functions/auth/_middleware.ts", "functions/middleware.ts", "functions/api.ts"], {B: ["functions/api.ts"]}),
 ("X17 security/ alla radice con migrations/ dentro", ["security/migrations/1.sql", "security/policy.py"], {}),
 ("X18 web/auth/login.tsx trovato da frontend (cartella web/ alla radice)", ["web/auth/login.tsx", "web/index.html"], {F: ["web/auth/login.tsx"]}),
 ("X19 middleware.ts sotto supabase/ annidata e sotto migrations/", ["apps/api/supabase/middleware.ts", "db/migrations/middleware.ts", "db/migrations/1.sql"], {}),
 ("X20 src/auth/llm/middleware.ts (cartella di ai dentro auth, nome di security)", ["src/auth/llm/middleware.ts", "src/auth/llm/client.py", "src/auth/a.py"], {}),
 ("X21 solo un marcatore di security in un file sotto components/", ["src/components/Token.tsx", "src/components/A.tsx"], {S: ["src/components/Token.tsx"]}),
 ("X22 file trovato da security dentro auth/ e da frontend: tre vie", ["src/auth/Guard.tsx", "src/auth/x.ts"], {F: ["src/auth/Guard.tsx"], S: ["src/auth/Guard.tsx"]}),
]

def main() -> int:
    ap = argparse.ArgumentParser(); ap.add_argument("--codice", required=True)
    code = Path(ap.parse_args().codice).resolve()
    sys.path.insert(0, str(code / "bin"))
    from tollgate_analysis import profiles
    from tollgate_core import fragments, git
    from tollgate_flow import init
    base = (code / "templates" / "tollgate.toml").read_text(encoding="utf-8").replace("__MODE__", "detect")
    tmp = tempfile.TemporaryDirectory(prefix="tollgate-sonda-finale-")
    priv = Path(tmp.name)
    def root_with(edit=None, drop=False):
        """Una radice di plugin: frammenti, skill e agenti veri; `edit` riscrive security.toml."""
        r = Path(tempfile.mkdtemp(prefix="radice-", dir=priv))
        shutil.copytree(code / "templates", r / "templates"); shutil.copytree(code / "skills", r / "skills")
        shutil.copytree(code / "agents", r / "agents")
        f = r / "templates" / "profiles" / "security.toml"
        if drop: f.unlink()
        elif edit: f.write_text(edit(f.read_text(encoding="utf-8")), encoding="utf-8")
        return r
    real = root_with()
    nokeep = root_with(lambda t: t.replace("keep_paths = true", "keep_paths = false"))
    nosec = root_with(drop=True)
    assert not [f for f in fragments.load(nokeep) if f.area == S][0].keep_paths
    def run(root, files, detected):
        got = init.profile_blocks({f: 10 for f in files}, base, root, detected=detected or None)
        decl = {k: v for k, v in tomllib.loads(base + got.text).get("profiles", {}).items() if isinstance(v, dict)}
        return ({a: sorted(p["paths"]) for a, p in decl.items()},
                {f: profiles.vertical_for(f, decl) for f in files},
                {f: sorted(profiles.active_profiles([f], decl, [])) for f in files}, decl, got)
    print("== parte 1: casi nuovi")
    for name, files, det in CASES:
        p, r, a, decl, _ = run(real, files, det)
        bad = "security" in decl and "final_specialist" not in decl["security"]
        print(f"{name}\n   file: {files}\n   trovati: {det}\n   proposta: {p}\n   runtime: {r}\n   attivi: { {f: v for f, v in a.items() if len(v) > 1} }" + ("\n   !! security senza final_specialist" if bad else ""))
        for f in files:
            if f.startswith("supabase/") and (r[f] == S or S in a[f]):
                print(f"   !! {f} sotto supabase/ alla radice tocca security")
    # parte 2
    print("== parte 2: keep_paths e gli altri frammenti")
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "sonda-preflight"))
    import sonda
    allc = [(c[0], c[1], c[2]) for c in sonda.CASES + sonda.EXTRA] + CASES
    diff_keep = diff_sec = 0
    for name, files, det in allc:
        p1 = run(real, files, det)[0]; p2 = run(nokeep, files, det)[0]
        det3 = {k: v for k, v in det.items() if k != S}
        p3 = run(nosec, files, det3)[0]
        o1 = {k: v for k, v in p1.items() if k != S}; o2 = {k: v for k, v in p2.items() if k != S}
        if o1 != o2:
            diff_keep += 1; print(f"   !! {name.split()[0]}: keep_paths cambia gli altri blocchi: {o2} -> {o1}")
        # senza il frammento (e senza i suoi file rilevati) gli altri blocchi devono restare uguali
        # salvo dove `taken` di security toglieva un file a un altro (regola di I-1, attesa)
        if o1 != p3:
            diff_sec += 1; print(f"   nota {name.split()[0]}: con security gli altri blocchi cambiano: senza {p3}, con {o1} (trovati: {det})")
    print(f"   casi {len(allc)}: keep_paths cambia gli altri blocchi in {diff_keep}; il frammento li cambia in {diff_sec}")
    # parte 3: rilevamento vero
    print("== parte 3: rilevamento vero con git grep")
    repo = priv / "repo"; repo.mkdir()
    tree = {
     "src/lib/token.ts": "import jwt from 'jsonwebtoken'\n",
     "src/lib/esm.ts": "import { sign } from 'jsonwebtoken'\n",
     "src/x.test.ts": "import bcrypt from 'bcrypt'\n",
     "tests/test_jwt.py": "import jwt\n",
     "docs/guida.md": "import bcrypt\n",
     "supabase/functions/login/index.ts": "import { jwtVerify } from 'jose'\n",
     "web2/decode.tsx": "import jwtDecode from 'jwt-decode'\n",
     "app/commento.py": "# qui non si usa: import jwt\n",
     "app/utils.py": "import bcrypt_utils\n",
     "app/hash.py": "from passlib.hash import argon2\n",
     "app/std.py": "import hmac, hashlib\n",
     "app/nextauth.ts": "import NextAuth from 'next-auth'\n",
     "app/iron.ts": 'import { getIronSession } from "iron-session"\n',
     "app/joseedge.ts": "import * as jose from 'jose'\n",
     "app/req.js": "const a = require( 'bcrypt' )\n",
     "app/dyn.ts": "const jose = await import('jose')\n",
     "app/session.ts": "export const s = 1\n",
     "scripts/mock_auth.py": "import jwt\n",
     "app/server.ts": "import express from 'express'\nimport bcrypt from 'bcrypt'\n",
    }
    for rel, text in tree.items():
        (repo / rel).parent.mkdir(parents=True, exist_ok=True); (repo / rel).write_text(text, encoding="utf-8")
    env = {**os.environ, "GIT_CONFIG_GLOBAL": "/dev/null", "GIT_CONFIG_SYSTEM": "/dev/null"}
    for cmd in (["git", "init", "-q", "-b", "main", "."], ["git", "add", "-A"],
                ["git", "-c", "user.name=prova", "-c", "user.email=prova@example.com", "-c", "commit.gpgsign=false", "commit", "-qm", "x"]):
        subprocess.run(cmd, cwd=repo, check=True, env=env)
    sizes = git.tree_sizes_at(repo, "HEAD")
    warnings = []
    det = init.detect_files(repo, "HEAD", fragments.load_approved(real), sizes, warnings)
    print(f"   avvisi: {warnings}")
    print(f"   trovati da security: {det.get(S)}")
    print(f"   trovati da altri: { {k: v for k, v in det.items() if k != S and v} }")
    got = init.profile_blocks(sizes, base, real, detected=det)
    decl = {k: v for k, v in tomllib.loads(base + got.text).get('profiles', {}).items() if isinstance(v, dict)}
    print(f"   proposta: { {a: sorted(p['paths']) for a, p in decl.items()} }")
    print(f"   runtime: { {f: profiles.vertical_for(f, decl) for f in sorted(tree)} }")
    # parte 4: il repo di tollgate stesso
    print("== parte 4: i file della copia di tollgate che accendono security")
    env2 = env
    sizes = git.tree_sizes_at(code, "HEAD")
    det = init.detect_files(code, "HEAD", fragments.load_approved(real), sizes, [])
    got = init.profile_blocks(sizes, base, real, detected=det)
    decl = {k: v for k, v in tomllib.loads(base + got.text).get('profiles', {}).items() if isinstance(v, dict)}
    print(f"   trovati per contenuto da security: {det.get(S)}")
    print(f"   paths di security: {decl.get(S, {}).get('paths')}")
    # parte 5: deriva con security già dichiarato
    print("== parte 5: deriva (security già dichiarato)")
    cur = base + '\n[profiles.security]\npaths = ["src/auth/**"]\nrules = []\nblocking_rules = []\n'
    files = ["src/auth/a.ts", "src/middleware.ts", "supabase/functions/auth/index.ts", "server/auth/x.ts", "server/app.ts"]
    got = init.profile_blocks({f: 10 for f in files}, cur, real, detected={B: ["src/middleware.ts", "server/auth/x.ts", "server/app.ts"]})
    for l in got.lines:
        if "security" in l and "paths" in l: print("   " + l)
    tmp.cleanup(); return 0
if __name__ == "__main__":
    sys.exit(main())
