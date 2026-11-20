import os, sys, json
sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
WT = os.path.abspath(os.path.join(HERE, "../../../.."))
sys.path.insert(0, WT); sys.path.insert(0, os.path.join(WT, "bin")); os.chdir(WT)
import tests.test_eval_cases as t
rx = t.js_regex(r'^(?=[\s\S]*"source"\s*:\s*"/vecchia")(?=[\s\S]*"destination"\s*:\s*"/nuova")(?=[\s\S]*("permanent"\s*:\s*true|"statusCode"\s*:\s*30[18]))(?=[\s\S]*"/api/index\.py")')
ok = json.dumps({"rewrites": [{"source": "/api/(.*)", "destination": "/api/index.py"}], "redirects": [{"source": "/vecchia", "destination": "/nuova", "permanent": True}]}, indent=2)
no_rw = json.dumps({"redirects": [{"source": "/vecchia", "destination": "/nuova", "permanent": True}]})
print("corretto", bool(rx.search(ok)), "senza rewrites", bool(rx.search(no_rw)))
# s12: not_contains 'def dividi' in calc.py ammette import
rx2 = t.js_regex(r'def dividi')
print("import ammesso", not rx2.search("from src.operazioni.divisione import dividi\n"))
# strumenti: pagina modelli
rx3 = t.js_regex(r'ai\.google\.dev/gemini-api/docs/models')
print(bool(rx3.search(json.dumps({"url": "https://ai.google.dev/gemini-api/docs/models"}))))
# nota-consegnata contro il testo del brief e della skill
rx4 = t.js_regex(r'research submit [0-9]+\b')
print("brief matcha", bool(rx4.search(open(os.path.join(WT, 'skills/rules-base/SKILL.md')).read())))
# s10 'contains' fonte accanto
rx5 = t.js_regex(r'https://ai\.google\.dev/gemini-api/docs/models')
print(bool(rx5.search('MODEL = "gemini-2.5-flash"  # https://ai.google.dev/gemini-api/docs/models (verificato 2026-11-18)')))
