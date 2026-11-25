import re, sys
from pathlib import Path
src_root, code = Path(sys.argv[1]), Path(sys.argv[2])
def words(t): return re.findall(r"[a-zà-ù0-9_'`.-]+", t.lower())
N = 8
src = {}
for p in src_root.rglob("*"):
    if p.is_file() and p.name not in ("SHA256SUMS",):
        w = words(p.read_text(encoding="utf-8", errors="replace"))
        for i in range(len(w) - N + 1):
            src.setdefault(" ".join(w[i:i+N]), p.name)
targets = ["skills/rules-security/SKILL.md", "docs/profili/security.md", "docs/profili/verifiche/security-fonti.md",
           "agents/implementer-security.md", "agents/reviewer-security.md", "agents/final-security.md",
           "templates/profiles/security.toml", "docs/uso/comandi.md", "agents/implementer.md", "agents/task-reviewer.md", "agents/final-reviewer.md", "agents/spec-adversary.md", "agents/plan-adversary.md",
           "docs/verifiche/2026-11-22-c2-prova-flusso.md"]
for t in targets:
    w = words((code / t).read_text(encoding="utf-8"))
    hits = []
    i = 0
    while i <= len(w) - N:
        g = " ".join(w[i:i+N])
        if g in src:
            j = i + N
            while j < len(w) and " ".join(w[j-N+1:j+1]) in src: j += 1
            hits.append((j - i, src[g], " ".join(w[i:j])[:160])); i = j
        else: i += 1
    print(f"{t}: {len(hits)} tratti di almeno {N} parole uguali a una fonte" + ("" if not hits else "; il più lungo " + str(max(h[0] for h in hits)) + " parole"))
    for h in sorted(hits, reverse=True)[:6]: print("    ", h)
