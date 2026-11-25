import sys, tomllib
from pathlib import Path
sys.dont_write_bytecode = True
code = Path(sys.argv[1]); sys.path.insert(0, str(code / "bin"))
from tollgate_analysis import profiles
from tollgate_flow import init
base = (code / "templates" / "tollgate.toml").read_text(encoding="utf-8").replace("__MODE__", "detect")
for name, files, det in [
    ("X23 .tsx dentro auth/ trovato dal solo frontend", ["src/auth/Guard.tsx", "src/auth/x.ts"], {"frontend": ["src/auth/Guard.tsx"]}),
    ("X24 middleware.ts dentro auth/routes/", ["src/auth/routes/middleware.ts", "src/auth/a.ts"], {}),
    ("X25 migrazione .sql trovata da nessuno sotto auth/migrations e supabase annidata in auth", ["services/auth/migrations/1.sql", "services/auth/main.go"], {}),
]:
    got = init.profile_blocks({f: 10 for f in files}, base, code, detected=det or None)
    decl = {k: v for k, v in tomllib.loads(base + got.text).get("profiles", {}).items() if isinstance(v, dict)}
    print(name, "| proposta:", {a: sorted(p["paths"]) for a, p in decl.items()}, "| runtime:", {f: profiles.vertical_for(f, decl) for f in files}, "| attivi:", {f: sorted(profiles.active_profiles([f], decl, [])) for f in files})
