# tollgate P0: verifiche di piattaforma

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.
>
> **Nota per questo piano.** P0 non produce codice di tollgate: produce **fatti**. Alcuni passi sono interattivi e li esegue l'utente (marcati **[UTENTE]**). I passi che creano repo su GitHub si fermano e chiedono conferma (marcati **[CONFERMA]**). Esecuzione consigliata: nella sessione principale (executing-plans), non con subagenti.

**Goal:** Verificare le 13 voci «Ancora da verificare» della sezione 16 della spec, prima di scrivere codice, e aggiornare la spec dove un esito cambia il disegno.

**Architecture:** Un plugin sonda (`spikes/hookprobe/`) registra in un file JSONL l'input di ogni evento hook di Claude Code e, a richiesta, nega un comando. Gli esperimenti sugli hook girano con `claude -p --plugin-dir`; quelli interattivi li esegue l'utente. Gli esperimenti GitHub usano due repo di prova (uno privato, uno pubblico) con workflow minimi. Gli esperimenti JUnit usano tre progetti giocattolo in una cartella temporanea.

**Tech Stack:** Claude Code 2.1.294, bash, `jq`, `gh` 2.46, Python 3.13, Node 26 (vitest, jest), pytest.

**Spec:** `docs/superpowers/specs/2026-10-08-tollgate-nucleo-design.md` (revisione 14), sezione 16.

## Global Constraints

- Nessun codice di tollgate in P0: solo sonde usa e getta in `spikes/` e un rapporto.
- Le uscite grezze vanno in `$P0=/tmp/tollgate-p0` (fuori dal repo); nel repo vanno solo sonde e rapporto.
- Nessun repo GitHub si crea senza conferma esplicita dell'utente.
- Nessun segreto nei log: la sonda registra l'input degli hook, che non contiene token; non si registra l'ambiente.
- Rapporto in italiano, identificatori in inglese.
- Commit dopo ogni task.

## Review Focus

1. **Esito ambiguo registrato come certo.** Se un esperimento non dà un risultato netto (evento assente per un motivo diverso da quello ipotizzato), il rapporto scrive «non determinato» e il perché, non un sì o un no.
2. **Differenza tra `-p` e sessione interattiva.** Un comportamento visto con `claude -p` può non valere in sessione interattiva (e viceversa): il rapporto indica sempre in quale modalità è stato visto.
3. **Versione.** Ogni esito vale per Claude Code 2.1.294 e `gh` 2.46: il rapporto lo scrive in testa.
4. **Repo di prova lasciati in giro.** L'ultimo task propone all'utente di cancellarli; non li cancella da solo.
5. **Esito che smentisce la spec.** Se un fatto contraddice la spec, il task finale lo porta in una revisione 15 e non lo lascia solo nel rapporto.

---

### Task 1: Plugin sonda

**Files:**
- Create: `spikes/hookprobe/.claude-plugin/plugin.json`
- Create: `spikes/hookprobe/hooks/hooks.json`
- Create: `spikes/hookprobe/probe.sh`
- Create: `spikes/hookprobe/skills/probe-only-user/SKILL.md`
- Create: `spikes/hookprobe/skills/probe-worktree/SKILL.md`
- Test: `spikes/hookprobe/test-probe.sh`

**Interfaces:**
- Produces: `probe.sh <EVENTO>` legge il JSON da stdin e aggiunge a `$PROBE_LOG` (predefinito `/tmp/tollgate-p0/probe.jsonl`) una riga `{"event": "<EVENTO>", "input": <json>}`. Se l'evento è `PreToolUse` e l'input contiene la stringa `PROBE_DENY`, stampa `probe deny` su stderr ed esce con 2. Altrimenti esce con 0.

- [ ] **Step 1: Scrivere il test della sonda**

```bash
#!/usr/bin/env bash
# spikes/hookprobe/test-probe.sh
set -euo pipefail
here="$(cd "$(dirname "$0")" && pwd)"
export PROBE_LOG="$(mktemp)"
echo '{"tool_name":"Bash","tool_input":{"command":"echo ok"}}' | "$here/probe.sh" PreToolUse
rc_ok=$?
set +e
echo '{"tool_name":"Bash","tool_input":{"command":"echo PROBE_DENY"}}' | "$here/probe.sh" PreToolUse 2>/dev/null
rc_deny=$?
set -e
lines=$(wc -l < "$PROBE_LOG")
first_event=$(head -1 "$PROBE_LOG" | jq -r .event)
[ "$rc_ok" -eq 0 ] && [ "$rc_deny" -eq 2 ] && [ "$lines" -eq 2 ] && [ "$first_event" = "PreToolUse" ] \
  && echo "PASS" || { echo "FAIL rc_ok=$rc_ok rc_deny=$rc_deny lines=$lines event=$first_event"; exit 1; }
```

- [ ] **Step 2: Eseguire il test e vederlo fallire**

Run: `chmod +x spikes/hookprobe/test-probe.sh && spikes/hookprobe/test-probe.sh`
Expected: errore «probe.sh: No such file or directory».

- [ ] **Step 3: Scrivere la sonda**

```bash
#!/usr/bin/env bash
# spikes/hookprobe/probe.sh — registra l'input di un hook; nega i PreToolUse con PROBE_DENY
event="${1:-unknown}"
log="${PROBE_LOG:-/tmp/tollgate-p0/probe.jsonl}"
mkdir -p "$(dirname "$log")"
input="$(cat)"
printf '%s' "$input" | jq -c --arg e "$event" '{event: $e, input: .}' >> "$log"
if [ "$event" = "PreToolUse" ] && printf '%s' "$input" | grep -q 'PROBE_DENY'; then
  echo "probe deny" >&2
  exit 2
fi
exit 0
```

```json
{
  "name": "hookprobe",
  "version": "0.0.1",
  "description": "Sonda usa e getta per le verifiche P0 di tollgate"
}
```

`hooks/hooks.json` (un blocco per evento, senza matcher così scatta su tutto):

```json
{
  "hooks": {
    "SessionStart":        [{"hooks": [{"type": "command", "command": "${CLAUDE_PLUGIN_ROOT}/probe.sh SessionStart"}]}],
    "UserPromptSubmit":    [{"hooks": [{"type": "command", "command": "${CLAUDE_PLUGIN_ROOT}/probe.sh UserPromptSubmit"}]}],
    "UserPromptExpansion": [{"hooks": [{"type": "command", "command": "${CLAUDE_PLUGIN_ROOT}/probe.sh UserPromptExpansion"}]}],
    "PreToolUse":          [{"matcher": "*", "hooks": [{"type": "command", "command": "${CLAUDE_PLUGIN_ROOT}/probe.sh PreToolUse"}]}],
    "PostToolUse":         [{"matcher": "*", "hooks": [{"type": "command", "command": "${CLAUDE_PLUGIN_ROOT}/probe.sh PostToolUse"}]}],
    "SubagentStart":       [{"hooks": [{"type": "command", "command": "${CLAUDE_PLUGIN_ROOT}/probe.sh SubagentStart"}]}],
    "SubagentStop":        [{"hooks": [{"type": "command", "command": "${CLAUDE_PLUGIN_ROOT}/probe.sh SubagentStop"}]}]
  }
}
```

`skills/probe-only-user/SKILL.md`:

```markdown
---
name: probe-only-user
description: Sonda P0. Rispondi solo "probe-only-user eseguita".
disable-model-invocation: true
---
Rispondi esattamente: probe-only-user eseguita
```

`skills/probe-worktree/SKILL.md`:

```markdown
---
name: probe-worktree
description: Sonda P0 per EnterWorktree.
disable-model-invocation: true
---
Usa lo strumento EnterWorktree per entrare nel worktree il cui percorso è scritto nel file /tmp/tollgate-p0/worktree-path.txt. Poi esegui `git rev-parse --abbrev-ref HEAD` e `pwd` con Bash e riporta l'output esatto. Se EnterWorktree rifiuta il percorso, riporta il messaggio d'errore esatto.
```

- [ ] **Step 4: Eseguire il test e vederlo passare**

Run: `chmod +x spikes/hookprobe/probe.sh && spikes/hookprobe/test-probe.sh`
Expected: `PASS`

- [ ] **Step 5: Verificare che Claude Code carichi la sonda**

Run: `mkdir -p /tmp/tollgate-p0 && rm -f /tmp/tollgate-p0/probe.jsonl && cd /tmp && claude -p --plugin-dir "$OLDPWD/spikes/hookprobe" "Rispondi solo: ok" && jq -r .event /tmp/tollgate-p0/probe.jsonl | sort | uniq -c`
Expected: almeno una riga `SessionStart` e una `UserPromptSubmit`. Se il file non esiste, il plugin non è stato caricato: fermarsi e annotare l'errore nel rapporto.

- [ ] **Step 6: Commit**

```bash
git add spikes/hookprobe
git commit -m "spike: plugin sonda per le verifiche P0"
```

---

### Task 2: Esperimenti sugli hook con `claude -p`

**Files:**
- Create: `spikes/run-hook-experiments.sh`
- Create: `docs/verifiche/2026-10-08-p0-esiti.md` (sezione «Hook»)

**Interfaces:**
- Consumes: `spikes/hookprobe/` (Task 1).
- Produces: `$P0/e<N>.jsonl` per ogni esperimento; righe del rapporto con esito `sì` / `no` / `non determinato`, modalità `-p` e versione.

Esperimenti (ognuno azzera il log e salva la copia):

| Id | Voce di 16 | Prompt / comando | Cosa leggere nel log |
|---|---|---|---|
| E1 | `SubagentStart`/`Stop` alla ripresa con `SendMessage`; campi di `SendMessage` | «Lancia con Agent un subagente general-purpose in background con il compito "rispondi uno". Quando ha finito, riprendilo con SendMessage chiedendo "rispondi due". Riporta entrambe le risposte.» | Numero di `SubagentStart` e `SubagentStop` (2 e 2 = scattano alla ripresa); `PreToolUse` con `tool_name == "SendMessage"` e le chiavi di `tool_input` |
| E2 | `SubagentHandback` e `last_assistant_message` | Come E1 senza ripresa, con `--permission-mode auto` | `PostToolUse` con `tool_name == "SubagentHandback"`; confronto fra il suo `tool_input` e `last_assistant_message` di `SubagentStop` |
| E3 | `deny` in `bypassPermissions` | «Esegui con Bash: echo PROBE_DENY > /tmp/tollgate-p0/e3-side.txt», con `--permission-mode bypassPermissions` | Il file `/tmp/tollgate-p0/e3-side.txt` **non** deve esistere |
| E4 | `UserPromptExpansion` con `disable-model-invocation`, forma lunga e breve, in `-p` | Prompt `/hookprobe:probe-only-user`, poi in un'altra esecuzione `/probe-only-user` | Presenza di `UserPromptExpansion` e valore di `expansion_type` per ciascuna forma |

- [ ] **Step 1: Scrivere lo script degli esperimenti**

```bash
#!/usr/bin/env bash
# spikes/run-hook-experiments.sh — esegue E1-E4 e salva i log in $P0
set -uo pipefail
P0=/tmp/tollgate-p0; mkdir -p "$P0"
PLUGIN="$(cd "$(dirname "$0")/hookprobe" && pwd)"
export PROBE_LOG="$P0/probe.jsonl"
run() { # id, mode, prompt
  rm -f "$PROBE_LOG"
  ( cd /tmp && claude -p --plugin-dir "$PLUGIN" --permission-mode "$2" "$3" ) > "$P0/$1.out" 2>&1
  cp "$PROBE_LOG" "$P0/$1.jsonl" 2>/dev/null || echo '' > "$P0/$1.jsonl"
}
run e1 manual "Lancia con lo strumento Agent un subagente general-purpose in background con il compito: rispondi solo 'uno'. Quando ha finito, riprendilo con lo strumento SendMessage chiedendo: rispondi solo 'due'. Riporta entrambe le risposte."
run e2 auto "Lancia con lo strumento Agent un subagente general-purpose con il compito: rispondi solo 'uno'. Riporta la risposta."
rm -f "$P0/e3-side.txt"
run e3 bypassPermissions "Esegui con Bash esattamente: echo PROBE_DENY > /tmp/tollgate-p0/e3-side.txt"
run e4-long manual "/hookprobe:probe-only-user"
run e4-short manual "/probe-only-user"
echo "fatto: $(ls "$P0")"
```

- [ ] **Step 2: Eseguire lo script**

Run: `chmod +x spikes/run-hook-experiments.sh && spikes/run-hook-experiments.sh`
Expected: `fatto:` seguito da `e1.jsonl e1.out e2.jsonl …`. Se `--permission-mode manual` non esiste, sostituirlo con `default` e annotarlo.

- [ ] **Step 3: Estrarre gli esiti**

Run:
```bash
P0=/tmp/tollgate-p0
echo "E1:"; jq -r .event $P0/e1.jsonl | sort | uniq -c
jq -c 'select(.event=="PreToolUse" and .input.tool_name=="SendMessage") | .input.tool_input | keys' $P0/e1.jsonl
echo "E2:"; jq -c 'select(.input.tool_name=="SubagentHandback") | {event, ti: .input.tool_input}' $P0/e2.jsonl
jq -c 'select(.event=="SubagentStop") | .input.last_assistant_message' $P0/e2.jsonl
echo "E3:"; test -e $P0/e3-side.txt && echo "ESEGUITO (deny NON rispettato)" || echo "non eseguito (deny rispettato)"
echo "E4:"; for f in e4-long e4-short; do echo $f; jq -c 'select(.event=="UserPromptExpansion") | .input | {expansion_type, prompt: (.prompt // .command_name // null)}' $P0/$f.jsonl; done
```
Expected: un output per ogni esperimento. Un output vuoto per E2 o E4 è un esito («l'evento non scatta»), da distinguere da un errore di esecuzione: controllare in `$P0/<id>.out` che Claude abbia davvero eseguito il compito.

- [ ] **Step 4: Scrivere la sezione «Hook» del rapporto**

Creare `docs/verifiche/2026-10-08-p0-esiti.md` con questa intestazione e una riga per esperimento, riempita con gli esiti reali dello Step 3:

```markdown
# Esiti delle verifiche P0

Versioni: Claude Code 2.1.294, gh 2.46.0, Python 3.13.5, Node 26.7.0. Data: <data di esecuzione>.

## Hook (claude -p)

| Id | Voce della spec (16) | Esito | Evidenza | Conseguenza per la spec |
|---|---|---|---|---|
| E1 | SubagentStart/Stop alla ripresa; campi di SendMessage | <sì/no/non determinato> | <conteggi e chiavi viste> | <nessuna / cosa cambia> |
| E2 | SubagentHandback e last_assistant_message | … | … | … |
| E3 | deny in bypassPermissions | … | … | … |
| E4 | UserPromptExpansion, disable-model-invocation, forma lunga e breve (-p) | … | … | … |
```

- [ ] **Step 5: Commit**

```bash
git add spikes/run-hook-experiments.sh docs/verifiche/2026-10-08-p0-esiti.md
git commit -m "verifiche P0: esiti degli esperimenti sugli hook"
```

---

### Task 3: Esperimenti interattivi [UTENTE]

**Files:**
- Modify: `docs/verifiche/2026-10-08-p0-esiti.md` (sezione «Interattivi»)

**Interfaces:**
- Consumes: `spikes/hookprobe/` (Task 1).

| Id | Voce di 16 | Cosa fa l'utente |
|---|---|---|
| I1 | comandi `!` e hook `PreToolUse` | In una sessione `claude --plugin-dir spikes/hookprobe` digita `! echo PROBE_DENY_BANG` |
| I2 | `UserPromptExpansion` in sessione interattiva, forma lunga e breve | Nella stessa sessione digita `/hookprobe:probe-only-user`, poi `/probe-only-user` |
| I3 | `EnterWorktree` dentro una skill | Digita `/hookprobe:probe-worktree` dopo che il coordinatore ha preparato il worktree (Step 1) |

- [ ] **Step 1: Preparare il worktree per I3**

Run:
```bash
rm -rf /tmp/tollgate-p0/wt-repo /tmp/tollgate-p0/wt-1
git init -q /tmp/tollgate-p0/wt-repo && cd /tmp/tollgate-p0/wt-repo && git commit -q --allow-empty -m init
git worktree add -q -b tg/1-probe /tmp/tollgate-p0/wt-1
echo /tmp/tollgate-p0/wt-1 > /tmp/tollgate-p0/worktree-path.txt
rm -f /tmp/tollgate-p0/probe.jsonl
```
Expected: nessun errore; `/tmp/tollgate-p0/wt-1` esiste sul ramo `tg/1-probe`.

- [ ] **Step 2: [UTENTE] Eseguire I1, I2, I3**

Chiedere all'utente di lanciare, in un terminale separato:

```bash
cd /tmp/tollgate-p0/wt-repo && PROBE_LOG=/tmp/tollgate-p0/probe.jsonl claude --plugin-dir "<percorso assoluto del repo>/spikes/hookprobe"
```

e di digitare nell'ordine: `! echo PROBE_DENY_BANG`, `/hookprobe:probe-only-user`, `/probe-only-user`, `/hookprobe:probe-worktree`, poi `/exit`. Attendere la conferma dell'utente.

- [ ] **Step 3: Estrarre gli esiti**

Run:
```bash
P0=/tmp/tollgate-p0; cp $P0/probe.jsonl $P0/interactive.jsonl
echo "I1:"; jq -c 'select(.event=="PreToolUse" and (.input|tostring|contains("PROBE_DENY_BANG")))' $P0/interactive.jsonl | head -3
echo "I2:"; jq -c 'select(.event=="UserPromptExpansion") | .input | {expansion_type}' $P0/interactive.jsonl
echo "I3:"; jq -c 'select(.input.tool_name=="EnterWorktree") | {event, ti: .input.tool_input, resp: .input.tool_response}' $P0/interactive.jsonl
```
Expected: I1 vuoto = i comandi `!` non passano da `PreToolUse`; I2 una riga per forma = l'evento scatta; I3 mostra se `EnterWorktree` ha accettato il percorso. Chiedere all'utente anche cosa ha visto a schermo per I1 (il comando è stato eseguito?) e per I3 (il ramo riportato).

- [ ] **Step 4: Scrivere la sezione «Interattivi» del rapporto**

Aggiungere al rapporto la tabella con le colonne di Task 2 (Id, Voce, Esito, Evidenza, Conseguenza) e le righe I1-I3.

- [ ] **Step 5: Salvare gli input reali degli hook come fixture per P2**

I test degli hook di P2 devono usare input veri di Claude Code, non inventati (piano principale, sezione 5). Si salva un esempio per ogni coppia evento/strumento vista, con i percorsi della home sostituiti.

Run:
```bash
mkdir -p spikes/fixtures/hook-inputs
cat /tmp/tollgate-p0/e*.jsonl /tmp/tollgate-p0/interactive.jsonl 2>/dev/null \
  | jq -c 'select(.event) | {key: (.event + "-" + (.input.tool_name // "none")), value: .input}' \
  | jq -s 'map({(.key): .value}) | add' \
  | sed "s#$HOME#/home/USER#g" > spikes/fixtures/hook-inputs/samples.json
jq 'keys' spikes/fixtures/hook-inputs/samples.json
```
Expected: un elenco di chiavi come `PreToolUse-Bash`, `SubagentStart-none`, `UserPromptExpansion-none`. Controllare a occhio che il file non contenga token o contenuti personali; se ne contiene, toglierli prima del commit.

- [ ] **Step 6: Commit**

```bash
git add docs/verifiche/2026-10-08-p0-esiti.md spikes/fixtures/hook-inputs/samples.json
git commit -m "verifiche P0: esiti degli esperimenti interattivi e fixture degli hook"
```

---

### Task 4: Report JUnit di vitest, jest e pytest

**Files:**
- Create: `spikes/junit/make-projects.sh`
- Modify: `docs/verifiche/2026-10-08-p0-esiti.md` (sezione «JUnit»)

**Interfaces:**
- Produces: per ogni strumento, due report JUnit di due esecuzioni consecutive in `$P0/junit/<tool>/run1.xml` e `run2.xml`; la regola di identificativo `<classname>::<name>` e il modo in cui ciascuno scrive un test saltato.

- [ ] **Step 1: Scrivere lo script dei progetti giocattolo**

Ogni progetto ha tre test: uno che passa, uno saltato, uno che fallisce, dentro un gruppo `describe`/classe.

```bash
#!/usr/bin/env bash
# spikes/junit/make-projects.sh — crea ed esegue tre progetti giocattolo
set -uo pipefail
J=/tmp/tollgate-p0/junit; rm -rf "$J"; mkdir -p "$J"/{vitest,jest,pytest}

cd "$J/vitest" && npm init -y >/dev/null && npm i -D vitest@2 >/dev/null 2>&1
cat > sample.test.js <<'EOF'
import { describe, it, expect } from 'vitest'
describe('group', () => {
  it('passes', () => expect(1).toBe(1))
  it.skip('skipped', () => expect(1).toBe(2))
  it('fails', () => expect(1).toBe(2))
})
EOF
for r in 1 2; do npx vitest run --reporter=junit --outputFile="run$r.xml" >/dev/null 2>&1; done

cd "$J/jest" && npm init -y >/dev/null && npm i -D jest@29 jest-junit@16 >/dev/null 2>&1
cat > sample.test.js <<'EOF'
describe('group', () => {
  it('passes', () => expect(1).toBe(1))
  it.skip('skipped', () => expect(1).toBe(2))
  it('fails', () => expect(1).toBe(2))
})
EOF
for r in 1 2; do JEST_JUNIT_OUTPUT_NAME="run$r.xml" npx jest --reporters=default --reporters=jest-junit >/dev/null 2>&1; done

cd "$J/pytest" && python3 -m venv .venv && .venv/bin/pip -q install pytest >/dev/null 2>&1
cat > test_sample.py <<'EOF'
import pytest
class TestGroup:
    def test_passes(self): assert 1 == 1
    @pytest.mark.skip(reason="probe")
    def test_skipped(self): assert 1 == 2
    def test_fails(self): assert 1 == 2
EOF
for r in 1 2; do .venv/bin/pytest -q --junitxml="run$r.xml" >/dev/null 2>&1; done
ls "$J"/*/run*.xml
```

- [ ] **Step 2: Eseguire lo script**

Run: `chmod +x spikes/junit/make-projects.sh && spikes/junit/make-projects.sh`
Expected: sei file `run1.xml`/`run2.xml`. Se un'installazione fallisce per la rete, annotarlo e proseguire con gli altri.

- [ ] **Step 3: Estrarre identificativi e salti**

Run:
```bash
python3 - <<'EOF'
import xml.etree.ElementTree as ET, glob
for tool in ("vitest","jest","pytest"):
    ids=[]
    for run in ("run1","run2"):
        f=f"/tmp/tollgate-p0/junit/{tool}/{run}.xml"
        try: root=ET.parse(f).getroot()
        except Exception as e: print(tool, run, "ERRORE", e); continue
        cases=[(tc.get("classname"), tc.get("name"),
                "skipped" if tc.find("skipped") is not None else
                "failure" if tc.find("failure") is not None or tc.find("error") is not None else "ok")
               for tc in root.iter("testcase")]
        ids.append([(c,n) for c,n,_ in cases]); print(tool, run, cases)
    if len(ids)==2: print(tool, "identificativi stabili:", ids[0]==ids[1])
EOF
```
Expected: per ogni strumento tre `testcase` con stato `ok`, `skipped`, `failure`, e «identificativi stabili: True».

- [ ] **Step 4: Scrivere la sezione «JUnit» del rapporto**

Una riga per strumento: forma di `classname` e `name`, rappresentazione del salto, stabilità tra due esecuzioni, comando e reporter usati (diventano gli esempi di `[commands] report` in `init`).

- [ ] **Step 5: Commit**

```bash
git add spikes/junit/make-projects.sh docs/verifiche/2026-10-08-p0-esiti.md
git commit -m "verifiche P0: report JUnit di vitest, jest e pytest"
```

---

### Task 5: Tag di versione di Superpowers

**Files:**
- Modify: `docs/verifiche/2026-10-08-p0-esiti.md` (sezione «Superpowers»)

- [ ] **Step 1: Leggere i tag del repository dichiarato nel plugin**

Il campo `repository` di `~/.claude/plugins/cache/claude-plugins-official/superpowers/6.4.1/.claude-plugin/plugin.json` è `https://github.com/obra/superpowers`.

Run: `git ls-remote --tags https://github.com/obra/superpowers | grep -E 'v?6\.4' | head`
Expected: righe con tag `v6.4.x` o `6.4.x` → l'intervallo `>=6.4.1 <7.0.0` in `dependencies` è utilizzabile; nessuna riga → vale il ripiego di 11.1 (controllo della versione in `start`).

- [ ] **Step 2: Scrivere la sezione «Superpowers» e committare**

```bash
git add docs/verifiche/2026-10-08-p0-esiti.md
git commit -m "verifiche P0: tag di versione di Superpowers"
```

---

### Task 6: Esperimenti GitHub [CONFERMA]

**Files:**
- Create: `spikes/gh/workflows/probe-run.yml`
- Create: `spikes/gh/workflows/probe-verdict.yml`
- Create: `spikes/gh/workflows/probe-verdict-noactions.yml`
- Create: `spikes/gh/workflows/probe-target.yml`
- Create: `spikes/gh/run-gh-experiments.sh`
- Modify: `docs/verifiche/2026-10-08-p0-esiti.md` (sezione «GitHub»)

**Interfaces:**
- Produces: esiti G1-G5 nel rapporto.

| Id | Voce di 16 | Esperimento |
|---|---|---|
| G1 | rulesets e GET di protezione su privato Free | Su `tollgate-probe` privato: piano dell'account, GET di protezione, POST di un ruleset con `required_status_checks` |
| G2 | `actions: read` in `workflow_run` per gli artefatti | `probe-run` (pull_request) carica un artefatto; `probe-verdict` (con `actions: read`) e `probe-verdict-noactions` (senza) lo scaricano |
| G3 | `pull_request_target` verso un ramo non predefinito | PR verso il ramo `other`; `probe-target` scatta? Con quale definizione? |
| G4 | sorgente fissata per gli stati di commit | Su `tollgate-probe-public`: protezione con `checks: [{context: "tollgate/verdict", app_id: <id dell'app GitHub Actions>}]`; uno stato `tollgate/verdict` pubblicato con il token personale soddisfa la protezione? |
| G5 | permessi di Dependabot per `workflow_run` | Solo documentazione: pagina di GitHub su Dependabot e Actions, citata nel rapporto |

- [ ] **Step 1: [CONFERMA] Chiedere all'utente il permesso di creare i repo**

Chiedere: «Creo sul tuo account GitHub due repo di prova, `tollgate-probe` (privato) e `tollgate-probe-public` (pubblico, vuoto salvo i workflow di prova)? Li cancelliamo alla fine.» Senza un sì esplicito, saltare G1-G4 e scrivere nel rapporto «non eseguito: manca il consenso».

- [ ] **Step 2: Scrivere i workflow di prova**

`spikes/gh/workflows/probe-run.yml`:

```yaml
name: probe-run
on: pull_request
permissions: { contents: read }
jobs:
  run:
    runs-on: ubuntu-latest
    steps:
      - run: echo "head=${{ github.event.pull_request.head.sha }}" > result.txt
      - uses: actions/upload-artifact@v4
        with: { name: probe-result, path: result.txt }
```

`spikes/gh/workflows/probe-verdict.yml`:

```yaml
name: probe-verdict
on:
  workflow_run:
    workflows: [probe-run]
    types: [completed]
permissions: { contents: read, actions: read, statuses: write }
jobs:
  verdict:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/download-artifact@v4
        with:
          name: probe-result
          run-id: ${{ github.event.workflow_run.id }}
          github-token: ${{ github.token }}
      - run: cat result.txt
```

`spikes/gh/workflows/probe-verdict-noactions.yml`: identico a `probe-verdict.yml` con `name: probe-verdict-noactions` e `permissions: { contents: read, statuses: write }`.

`spikes/gh/workflows/probe-target.yml`:

```yaml
name: probe-target
on: pull_request_target
permissions: { contents: read }
jobs:
  t:
    runs-on: ubuntu-latest
    steps:
      - run: echo "base=${{ github.event.pull_request.base.ref }} workflow_sha=${{ github.workflow_sha }}"
```

- [ ] **Step 3: Scrivere lo script degli esperimenti**

```bash
#!/usr/bin/env bash
# spikes/gh/run-gh-experiments.sh — G1-G4; richiede il consenso dello Step 1
set -uo pipefail
here="$(cd "$(dirname "$0")" && pwd)"; P0=/tmp/tollgate-p0/gh; rm -rf "$P0"; mkdir -p "$P0"
owner="$(gh api user --jq .login)"
gh api user --jq '.plan.name' > "$P0/g1-plan.txt" 2>&1

setup_repo() { # nome, visibilità
  gh repo create "$owner/$1" --"$2" --add-readme >/dev/null
  rm -rf "$P0/$1"; gh repo clone "$owner/$1" "$P0/$1" -- -q
  mkdir -p "$P0/$1/.github/workflows"; cp "$here"/workflows/*.yml "$P0/$1/.github/workflows/"
  ( cd "$P0/$1" && git add -A && git commit -qm "probe workflows" && git push -q )
}
setup_repo tollgate-probe private
setup_repo tollgate-probe-public public

# G1: protezione e ruleset sul privato
gh api "repos/$owner/tollgate-probe/branches/main/protection" > "$P0/g1-get.txt" 2>&1; echo "exit=$?" >> "$P0/g1-get.txt"
gh api -X POST "repos/$owner/tollgate-probe/rulesets" --input - > "$P0/g1-ruleset.txt" 2>&1 <<'EOF'
{"name":"probe","target":"branch","enforcement":"active",
 "conditions":{"ref_name":{"include":["~DEFAULT_BRANCH"],"exclude":[]}},
 "rules":[{"type":"required_status_checks","parameters":{"strict_required_status_checks_policy":true,
   "required_status_checks":[{"context":"tollgate/verdict"}]}}]}
EOF
echo "exit=$?" >> "$P0/g1-ruleset.txt"

# G2 e G3: PR verso main e verso other, sul privato
cd "$P0/tollgate-probe"
git switch -qc other && git push -qu origin other && git switch -q main
git switch -qc feature && echo x > x.txt && git add x.txt && git commit -qm x && git push -qu origin feature
gh pr create --base main --head feature --title probe-main --body probe >/dev/null
git switch -qc feature2 main && echo y > y.txt && git add y.txt && git commit -qm y && git push -qu origin feature2
gh pr create --base other --head feature2 --title probe-other --body probe >/dev/null
echo "attendere 3 minuti, poi lanciare lo Step 5"
```

- [ ] **Step 4: Eseguire lo script**

Run: `chmod +x spikes/gh/run-gh-experiments.sh && spikes/gh/run-gh-experiments.sh`
Expected: due repo creati, due PR aperte, «attendere 3 minuti».

- [ ] **Step 5: Raccogliere gli esiti di G1-G3**

Run:
```bash
P0=/tmp/tollgate-p0/gh; owner="$(gh api user --jq .login)"
echo "G1 piano:"; cat $P0/g1-plan.txt; echo "G1 GET:"; cat $P0/g1-get.txt; echo "G1 ruleset:"; cat $P0/g1-ruleset.txt
gh run list -R "$owner/tollgate-probe" --limit 20 --json name,event,conclusion,headBranch,databaseId > $P0/runs.json; cat $P0/runs.json
for id in $(jq -r '.[] | select(.name|startswith("probe-verdict")) | .databaseId' $P0/runs.json); do
  echo "--- run $id"; gh run view "$id" -R "$owner/tollgate-probe" --log 2>&1 | grep -E "head=|Error|error|403|Resource not accessible" | head -5
done
for id in $(jq -r '.[] | select(.name=="probe-target") | .databaseId' $P0/runs.json); do
  echo "--- target $id"; gh run view "$id" -R "$owner/tollgate-probe" --log 2>&1 | grep -E "base=" | head -2
done
```
Expected (da confrontare con il risultato reale): G1 GET con messaggio che cita l'upgrade del piano; G2 `probe-verdict` stampa `head=…`, `probe-verdict-noactions` fallisce con un errore di permesso; G3 una o due esecuzioni di `probe-target` con il loro `base=`.

- [ ] **Step 6: G4 sul repo pubblico**

Run:
```bash
P0=/tmp/tollgate-p0/gh; owner="$(gh api user --jq .login)"; R="$owner/tollgate-probe-public"
cd "$P0/tollgate-probe-public" && git switch -qc feature && echo x > x.txt && git add x.txt && git commit -qm x && git push -qu origin feature
gh pr create --base main --head feature --title g4 --body g4 >/dev/null; sleep 90
app_id=$(gh api "repos/$R/commits/$(git rev-parse HEAD)/check-runs" --jq '.check_runs[0].app.id'); echo "app_id Actions: $app_id" | tee $P0/g4.txt
gh api -X PUT "repos/$R/branches/main/protection" --input - >> $P0/g4.txt 2>&1 <<EOF
{"required_status_checks":{"strict":true,"checks":[{"context":"tollgate/verdict","app_id":$app_id}]},
 "enforce_admins":true,"required_pull_request_reviews":null,"restrictions":null}
EOF
gh api -X POST "repos/$R/statuses/$(git rev-parse HEAD)" -f state=success -f context=tollgate/verdict >/dev/null
sleep 10; gh pr view feature -R "$R" --json mergeStateStatus,statusCheckRollup | tee -a $P0/g4.txt
```
Expected: `app_id` numerico (letto dal check-run di `probe-run`, non scritto a mano); `mergeStateStatus` `BLOCKED` se la sorgente fissata esclude lo stato del token personale, `CLEAN` o `UNSTABLE` se lo accetta.

- [ ] **Step 7: G5 dalla documentazione**

Cercare su docs.github.com la pagina sull'uso di Dependabot con GitHub Actions (eventi `workflow_run` e permessi del token per le PR di Dependabot) e citarne la frase e l'URL nel rapporto. Se la pagina non chiarisce, esito «non determinato».

- [ ] **Step 8: Scrivere la sezione «GitHub» del rapporto e committare**

Tabella G1-G5 con le colonne di Task 2.

```bash
git add spikes/gh docs/verifiche/2026-10-08-p0-esiti.md
git commit -m "verifiche P0: esiti degli esperimenti GitHub"
```

---

### Task 7: Conseguenze per la spec e chiusura di P0

**Files:**
- Modify: `docs/superpowers/specs/2026-10-08-tollgate-nucleo-design.md` (sezione 16, e le sezioni che un esito smentisce)
- Modify: `docs/verifiche/2026-10-08-p0-esiti.md` (sezione «Conseguenze»)

- [ ] **Step 1: Elencare gli esiti che cambiano il disegno**

Rileggere la colonna «Conseguenza per la spec» del rapporto. Per ogni esito che smentisce la spec, scrivere nella sezione «Conseguenze» la sezione toccata e la modifica proposta. Casi già previsti:
- E1 «SubagentStart non scatta alla ripresa» → 6.3: i giri di correzione usano sempre un implementatore nuovo, e 7.2 perde la frase sulla ripresa;
- E2 «il report di SubagentHandback non è in last_assistant_message» → resta la lettura da `PostToolUse SubagentHandback` (7.2), confermata;
- E3 «deny non rispettato in bypassPermissions» → 1.2: limite dichiarato, e `start` avvisa se la sessione è in quella modalità;
- E4/I2 «UserPromptExpansion non scatta con disable-model-invocation» → 3 e 8.4: gli atti vanno registrati in un altro modo (decisione dell'utente);
- I1 «i comandi `!` non passano dagli hook» → 12.1: `db restore` resta da terminale; nessun'altra modifica;
- G1 → 9.3: risposta esatta per «non disponibile per il piano»;
- G2 «actions: read non basta / non serve» → 9.1;
- G4 «la sorgente fissata non vale per gli stati di commit» → 1.2 e criterio 10: limite dichiarato.

- [ ] **Step 2: [CONFERMA] Presentare le conseguenze all'utente**

Mostrare l'elenco e chiedere conferma prima di modificare la spec. Gli esiti che toccano una decisione dell'utente (E4/I2) richiedono una scelta esplicita.

- [ ] **Step 3: Aggiornare la spec**

Spostare le voci verificate da «Ancora da verificare» alla tabella «Verificato» della sezione 16 con data ed esito; applicare le modifiche approvate; aggiungere la riga 15 alla sezione 20.

- [ ] **Step 4: [CONFERMA] Proporre la cancellazione dei repo di prova**

Chiedere all'utente se cancellare `tollgate-probe` e `tollgate-probe-public`. Solo con un sì: `gh repo delete <owner>/tollgate-probe --yes` e lo stesso per il pubblico. Se `gh` non ha il permesso `delete_repo`, dare all'utente il comando `gh auth refresh -s delete_repo` da eseguire lui.

- [ ] **Step 5: Commit**

```bash
git add docs/superpowers/specs/2026-10-08-tollgate-nucleo-design.md docs/verifiche/2026-10-08-p0-esiti.md
git commit -m "spec: revisione 15 (esiti delle verifiche P0)"
```
