# Revisione Task 1 (P3a): verifiche di piattaforma

Pacchetto: 81ce50c..bc23a85. Log letti in /tmp/tollgate-p3a (v1.out/jsonl, v2.out, v3.out/jsonl/hs.txt, v4a/b/c.out, v5.out/jsonl, nb.json).

### Aderenza
- ✅ V1: `v1.jsonl` mostra `PreToolUse`/`PostToolUse Skill` con `hookprobe:probe-root`, `success:true`; `v1.out` riporta RADICE e SKILLDIR già espansi (percorsi con spazi). Evidenza letta, non dedotta. Nota: il log dice `permission_mode":"default"` mentre il rapporto scrive `--permission-mode manual` (è l'alias usato anche in P2: nessun problema).
- ✅ V2: `v2.out` contiene solo nomi; nessun valore (`AI_AGENT` e `OLDPWD` sono nominati come trovati per il valore, senza riportarlo). Rapporto e report coerenti. `CLAUDE_PLUGIN_ROOT` assente dall'elenco: confermato.
- ✅ V3: `v3.jsonl` `PostToolUse Bash` ha `stdout` = `session_id` di quella sessione (609be43e…), e `hs.txt` contiene lo stesso UUID; lo script cancella `hs.txt` prima, quindi il file è nato dall'hook prima del comando. Evidenza solida.
- ⚠️ V4: `v4a` (passa con 2+1 avvisi), `v4b` (`--strict` fallisce), `v4c` (passa) esistono. Ma `v4c.out` valida SOLO `marketplace.json`: manca il blocco «Validating plugin: .../plugin.json» presente in v4a/v4b. Il comando di v4c non è registrato e il blocco plugin sparito suggerisce un'invocazione diversa (sul file del marketplace, o plugin.json non più validato). Quindi «con author in plugin.json passa `--strict`» non è dimostrato dal log; è dimostrato solo che `description` radice + `author` in `plugins[0]` bastano per il marketplace.
- ✅ V5: `v5.jsonl` ha `PreToolUse NotebookEdit` con `notebook_path/new_source/cell_type/edit_mode`, `PostToolUse` con le chiavi citate, e `ToolSearch select:NotebookEdit` prima. Il campione in `samples.json` coincide con `nb.json`.
- ✅ Campione anonimizzato come gli altri: `transcript_path` con `/home/USER/...`, `cwd` `/tmp/tollgate-p3a` (come `/tmp/tollgate-p2/turns` nel campione P2); nessun dato personale. Il JSON resta valido.
- ✅ Ramo temporaneo di `probe.sh` tolto: `git diff main -- spikes/hookprobe/probe.sh` vuoto; il diff del commit non lo tocca. Working tree pulito; `mkt` rimosso (`git worktree list` mostra solo main e p3a); nessun `__pycache__` nel diff.
- ✅ Cautele: nessun segno di install/marketplace add; commit con i 4 file previsti.
- ⚠️ Riproducibilità: lo script lancia V1, V2, V3, V5 come nel brief, ma V3 senza il ramo temporaneo di `probe.sh` (tolto per requisito) non scrive `hs.txt`: lo script da solo non riproduce V3, e V4 non è nello script (dichiarato in intestazione). Né il ramo né i comandi di V4 sono riportati nel rapporto.

### Punti di forza
- Evidenze concrete con comandi citati; V3 verificata nel modo giusto (file cancellato prima, UUID corrispondente).
- V2 prudente: nessun valore, e la riserva su `CLAUDE_CODE_SESSION_ID` (uguaglianza non provata) è onesta.
- Percorso con spazi segnalato come conseguenza pratica per le skill.

### Rilievi
**Critical:** nessuno.

**Important**
- `docs/verifiche/2026-10-16-p3a-verifiche.md` riga V4 e Conseguenze V4: l'affermazione «`author` in `plugin.json` necessario/sufficiente per `--strict`» e l'istruzione «aggiungere `author` a `.claude-plugin/plugin.json`» poggiano su `v4c.out`, che non valida `plugin.json`. Il Task 10 erediterebbe una conseguenza non provata. Correzione: rilanciare `claude plugin validate --strict` su directory (non sul file) con `description` + `author` in `plugins[0]` e in `plugin.json`, e anche con `author` solo in `plugins[0]`; registrare il comando esatto e l'uscita completa (deve comparire il blocco «Validating plugin»). Se non si rilancia, riscrivere l'esito come «marketplace.json passa `--strict`; plugin.json non verificato con author».

**Minor**
- `spikes/run-p3a-experiments.sh`: per riprodurre V3 serve il ramo di `probe.sh`, assente; aggiungere nel rapporto (o come commento nello script) lo snippet del ramo e i comandi di V4, altrimenti l'esperimento non è ripetibile.
- Rapporto V2: «`CLAUDE_PLUGIN_ROOT` vale nelle skill e negli hook» — per le skill è provato da V1; per gli hook non è provato in questo task (V1 non lo mostra). Attenuare o citare la fonte (P0/P2).
- Rapporto V1: `<worktree>` sostituisce il percorso reale: va bene, ma ricordare che SKILLDIR è provato espanso solo nel testo letto dal modello, non in un hook.

### Valutazione
**Qualità del task:** Da correggere (lieve).
**Motivo:** V1, V2, V3, V5 sono sostenuti da evidenza reale e le cautele sono rispettate; V4 contiene una conseguenza (author in plugin.json per `--strict`) non supportata dal log `v4c.out`, che alimenta il Task 10, e va verificata o ridimensionata.
