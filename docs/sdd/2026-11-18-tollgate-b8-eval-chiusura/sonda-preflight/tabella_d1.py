"""Stampa la tabella Markdown della sonda: oggi, voluto, prototipo (processo separato per ciascun esito)."""
import os, sys, subprocess, json
sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import sonda_d1
from sonda_d1 import FORMS, asks
today = {text: asks(text) is not None for _, text, _ in FORMS}
import proto_b8
proto = {text: asks(text) is not None for _, text, _ in FORMS}
lab = lambda b: "chiede" if b else "passa"
rows = []
for tag, text, want in FORMS:
    rows.append((tag, text, today[text], want, proto[text]))
print("| # | Gruppo | Forma | Oggi | Piano | Già come voluto | Prototipo del piano |")
print("|---|---|---|---|---|---|---|")
for i, (tag, text, t, w, p) in enumerate(rows, 1):
    t_ = text.replace("|", "\\|")
    print(f"| {i} | {tag} | `{t_}` | {lab(t)} | {lab(w)} | {'sì' if t == w else 'no'} | {lab(p)}{'' if p == w else ' (DIVERSO)'} |")
n_ok = sum(1 for r in rows if r[2] == r[3])
print()
print(f"Totale forme: {len(rows)}; già come voluto oggi: {n_ok}; diverse oggi: {len(rows)-n_ok}; diverse con il prototipo: {sum(1 for r in rows if r[4]!=r[3])}.")
