### Task 1: Verifiche residue, formato d'uscita, campioni reali

Voci aperte della sezione 16 e fatti che il codice di P2 dà per buoni. Nessun codice di prodotto: un esperimento, un rapporto, la revisione 21 della spec.

**Files:**
- Create: `spikes/hookprobe/agents/probe-turns3.md`
- Create: `spikes/run-p2-experiments.sh`
- Create: `docs/verifiche/2026-10-09-p2-verifiche.md`
- Modify: `spikes/fixtures/hook-inputs/samples.json`
- Modify: `docs/superpowers/specs/2026-10-08-tollgate-nucleo-design.md` (revisione 21)

**Interfaces:**
- Produces: in `samples.json` le chiavi `PreToolUse-Write`, `PostToolUse-Write`, `PreToolUse-Edit`, `PostToolUse-Edit`, `PostToolUse-Skill` (sessione principale) e `PreToolUse-Write-subagent` (con `agent_id`). Le usano i Task 14-19 tramite `tests/hookkit.sample`.
- Produces: l'esito di D2 (quali eventi accettano `additionalContext`), che decide la tabella `INJECT_MODE` del Task 12.
- Produces: l'esito di D1, che decide il campo `version` di `dependencies` nel Task 13.

**Regole di cautela (vanno nel brief del subagente):** si lavora solo in `/tmp/tollgate-p2`. Non si installa, non si abilita e non si disinstalla nessun plugin nella configurazione dell'utente (niente `claude plugin install`, niente `claude plugin marketplace add`). Non si toccano `~/.claude/settings.json` né `~/.local/state/tollgate`. Non si crea nessun repo su GitHub. `claude -p` si lancia solo con `--plugin-dir spikes/hookprobe`.

- [ ] **Step 1: Agente sonda per il taglio durante la ripresa**

`spikes/hookprobe/agents/probe-turns3.md`:

```markdown
---
name: probe-turns3
description: Sonda P2 per maxTurns durante una ripresa. Da usare solo quando richiesto esplicitamente.
tools: Read
model: haiku
maxTurns: 3
---
Esegui alla lettera il compito che ricevi. Leggi i file solo con lo strumento Read, un file per turno. Alla fine di ogni compito scrivi FATTO.
```

- [ ] **Step 2: Script degli esperimenti**

`spikes/run-p2-experiments.sh` (eseguibile):

```bash
#!/usr/bin/env bash
# spikes/run-p2-experiments.sh — E7 (taglio in background), E8 (taglio alla ripresa), E9 (campioni)
set -uo pipefail
P2=/tmp/tollgate-p2; mkdir -p "$P2" || exit 1
PLUGIN="$(cd "$(dirname "$0")/hookprobe" && pwd)" || exit 1
export PROBE_LOG="$P2/probe.jsonl"
W="$P2/turns"; rm -rf "$W"; mkdir -p "$W" || exit 1
for i in 1 2 3 4 5 6 7 8; do echo "contenuto $i" > "$W/$i.txt"; done
run() { # id, modo, prompt
  rm -f "$PROBE_LOG"
  ( cd "$W" && claude -p --plugin-dir "$PLUGIN" --permission-mode "$2" "$3" < /dev/null ) > "$P2/$1.out" 2>&1
  cp "$PROBE_LOG" "$P2/$1.jsonl" 2>/dev/null || : > "$P2/$1.jsonl"
}
run e7 manual "Lancia con lo strumento Agent il subagente hookprobe:probe-turns IN BACKGROUND (run_in_background: true) con il compito descritto nelle sue istruzioni. Aspetta la notifica di fine e riporta alla lettera ogni testo che ricevi, compresi gli avvisi di interruzione."
run e8 manual "Lancia con lo strumento Agent, in primo piano, il subagente hookprobe:probe-turns3 con name 'sonda3' e il compito: leggi 1.txt e scrivi FATTO. Poi riprendilo con SendMessage verso 'sonda3' chiedendo: leggi 2.txt, 3.txt, 4.txt, 5.txt, 6.txt uno per turno e scrivi FATTO. Riporta alla lettera ogni risposta e ogni avviso di interruzione."
run e9 manual "Esegui in ordine: 1) con lo strumento Write crea il file nota.txt con il testo 'uno'; 2) con lo strumento Edit sostituisci 'uno' con 'due' in nota.txt; 3) lancia con lo strumento Agent un subagente general-purpose in primo piano con il compito: con lo strumento Write crea sub.txt con il testo 'tre' e rispondi FATTO; 4) invoca con lo strumento Skill la skill hookprobe:probe-preload. Riporta l'esito di ogni passo."
echo "fatto: $(ls "$P2")"
```

- [ ] **Step 3: Eseguire e leggere i log**

Run: `bash spikes/run-p2-experiments.sh`
Expected: `fatto:` seguito da `e7.jsonl e7.out e8.jsonl e8.out e9.jsonl e9.out probe.jsonl turns`.

Poi, per ogni log: `python3 -c "import json,sys; [print(json.loads(l)['event'], json.loads(l)['input'].get('tool_name'), json.loads(l)['input'].get('agent_id')) for l in open(sys.argv[1]) if l.strip()]" /tmp/tollgate-p2/e7.jsonl` (stesso per `e8`, `e9`).

Da registrare:
- **E7**: compare `SubagentStop` per il subagente in background tagliato? Il testo del taglio arriva al coordinatore? Da quale evento si può leggere (nessuno, `PostToolUse` di qualche strumento, solo la notifica)? Il `PostToolUse Agent` è `async_launched`.
- **E8**: la ripresa con 5 letture e `maxTurns: 3` viene tagliata? (`maxTurns` riparte da zero alla ripresa se la ripresa arriva a 3 letture.) Quali eventi produce il taglio alla ripresa (`SubagentStop`? `PostToolUse SendMessage` con quale `tool_response`?)
- **E9**: input di `PreToolUse`/`PostToolUse` di `Write`, `Edit`, `Skill` della sessione principale e di `Write` del subagente.

Se un esperimento non dà un risultato leggibile (per esempio il processo `-p` chiude prima della notifica del background), ripeterlo una volta con una formulazione più esplicita e registrare «non determinato» se non basta. Non inventare un esito.

- [ ] **Step 4: Campioni in `samples.json`**

Aggiungere a `spikes/fixtures/hook-inputs/samples.json` le chiavi elencate in **Interfaces**, copiando l'input reale da `e9.jsonl` e sostituendo la cartella personale con `/home/USER` (stessa anonimizzazione dei campioni esistenti):

```bash
python3 - <<'PY'
import json, os, re
from pathlib import Path
p = Path("spikes/fixtures/hook-inputs/samples.json")
samples = json.loads(p.read_text())
home = os.path.expanduser("~")
rows = [json.loads(l) for l in open("/tmp/tollgate-p2/e9.jsonl") if l.strip()]
def pick(event, tool, sub):
    for r in rows:
        i = r["input"]
        if r["event"] == event and i.get("tool_name") == tool and bool(i.get("agent_id")) == sub:
            return json.loads(json.dumps(i).replace(home, "/home/USER"))
    return None
for key, (ev, tool, sub) in {
    "PreToolUse-Write": ("PreToolUse", "Write", False), "PostToolUse-Write": ("PostToolUse", "Write", False),
    "PreToolUse-Edit": ("PreToolUse", "Edit", False), "PostToolUse-Edit": ("PostToolUse", "Edit", False),
    "PostToolUse-Skill": ("PostToolUse", "Skill", False),
    "PreToolUse-Write-subagent": ("PreToolUse", "Write", True)}.items():
    s = pick(ev, tool, sub)
    if s is None:
        print("MANCA", key)
    else:
        samples[key] = s
p.write_text(json.dumps(samples, ensure_ascii=False, indent=2) + "\n")
PY
```

Expected: nessuna riga `MANCA`. Se una manca, ripetere E9; se manca ancora, registrarlo nel rapporto e nel ledger: `tests/hookkit.sample` costruisce quell'input dalla busta di `PreToolUse-Bash` con `tool_name` e `tool_input` della documentazione (Task 12).

- [ ] **Step 5: Fatti dalla documentazione ufficiale**

Con un subagente `claude-code-guide` (modello sonnet), leggere le pagine ufficiali `hooks`, `plugins/dependencies` e `plugins-reference` e rispondere, citando la frase e la pagina:

- **D1**: le `dependencies` con `version` (intervallo semver) si risolvono sui tag del repo della dipendenza; quale forma di tag (`v6.4.1`, `superpowers--v6.4.1`, altro)? Una dipendenza da un plugin di un altro marketplace richiede `allowCrossMarketplaceDependenciesOn`? Esiste un comando che valida `plugin.json` senza installare (`claude plugin validate`)?
- **D2**: per quali eventi `hookSpecificOutput.additionalContext` viene aggiunto al contesto del modello: `PreToolUse`, `PostToolUse`, `SessionStart`, `SubagentStart`, `UserPromptExpansion`? Per `SubagentStop`, l'uscita 2 impedisce la chiusura e passa stderr al subagente? Per `PostToolUse`, l'uscita 2 mostra stderr al modello?
- **D3**: nomi e campi degli strumenti `MultiEdit` e `NotebookEdit` nella versione attuale (esistono ancora? `tool_input.file_path` o `notebook_path`?).

Se la documentazione non risponde a D2 per `PreToolUse`, provarlo: aggiungere temporaneamente a `spikes/hookprobe/probe.sh` un ramo che, per `PreToolUse` di `Read` con `PROBE_CTX` nel percorso, stampi `{"hookSpecificOutput":{"hookEventName":"PreToolUse","additionalContext":"MARCATORE-CTX-77"}}`, lanciare `claude -p` chiedendo di leggere `/tmp/tollgate-p2/turns/PROBE_CTX.txt` e di riportare ogni marcatore ricevuto, poi togliere il ramo.

- [ ] **Step 6: Rapporto**

`docs/verifiche/2026-10-09-p2-verifiche.md` con la stessa forma del rapporto di P0: versioni (`claude --version`), una tabella con `Id | Voce | Esito (sì/no/non determinato) | Evidenza | Conseguenza` per E7, E8, E9, D1, D2, D3, e la sezione «Conseguenze per il piano P2» che dice:
- quale valore va in `INJECT_MODE` (Task 12) per ogni evento;
- quale `version` va in `dependencies` (Task 13): l'intervallo `>=6.4.1 <7.0.0` se D1 conferma tag compatibili, altrimenti nessun `version` e il ripiego di 11.1 (controllo in `start`, P3);
- se il taglio in background o alla ripresa si riconosce da un evento: se sì, quale riga va aggiunta al modulo `post_agent` del Task 18 (o a un modulo nuovo); se no, la rete resta `stale_minutes` (spec 6.3), e il rapporto lo dice.

- [ ] **Step 7: Revisione 21 della spec**

In `docs/superpowers/specs/2026-10-08-tollgate-nucleo-design.md`:
- intestazione: `Revisione: **21**: esiti delle verifiche P2 (docs/verifiche/2026-10-09-p2-verifiche.md); eventi d'ingresso post_agent e post_skill; record come operazione. Revisione 20: …` (il resto invariato);
- 3.2, «Eventi d'ingresso»: aggiungere `post_agent` e `post_skill` all'elenco;
- 3.2, «Decisioni»: `record <operazione> <data>`: un'operazione di un elenco chiuso del motore, che scrive anche il suo evento di 18.4;
- 16: spostare le due voci di «Ancora da verificare» nella tabella degli esiti, con l'esito di E7/E8 e di D1 (o «non determinato» con la rete di sicurezza);
- 20: una riga per la revisione 21.

- [ ] **Step 8: Commit**

```bash
git add spikes/hookprobe/agents/probe-turns3.md spikes/run-p2-experiments.sh spikes/fixtures/hook-inputs/samples.json docs/verifiche/2026-10-09-p2-verifiche.md docs/superpowers/specs/2026-10-08-tollgate-nucleo-design.md
git commit -m "tollgate P2: verifiche residue (maxTurns, dependencies, uscite degli hook), campioni reali, spec rev 21"
```

---

