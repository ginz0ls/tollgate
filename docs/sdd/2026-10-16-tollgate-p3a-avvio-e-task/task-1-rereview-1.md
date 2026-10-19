# Ri-revisione giro 1 del Task 1 (P3a)

Diff: bc23a85..c301c86 (solo `docs/verifiche/2026-10-16-p3a-verifiche.md`). Log letti: `/tmp/tollgate-p3a/v4-fix-a.out`, `v4-fix-b.out`.

### Verdetti sui rilievi
1. **(Important) V4: il log non dimostrava che serva `author` in `plugin.json` per `--strict`.** INDIRIZZATO. `v4-fix-b.out` (author solo in `plugins[0]`): avviso sul marketplace «plugins[0] plugin.json → author», blocco «Validating plugin: …/plugin.json» con avviso `author`, `Validation failed (--strict…)`, `rc=1`. `v4-fix-a.out` (author in entrambi): `✔ Validation passed`, `rc=0`. Il blocco «Validating plugin» assente in (a) è spiegato nel rapporto (compare solo con avvisi) ed è coerente con (b). Riga V4 e Conseguenze V4 (rapporto, righe V4 e «Conseguenze») ora allineate: `--strict` richiede author in entrambi i punti, il Task 10 aggiunge author a `plugin.json`. I comandi sono nel rapporto (`claude plugin validate [--strict] /tmp/tollgate-p3a/mkt`). Nota minima: i due log riportano solo uscita e rc, non il comando; il comando sta nel rapporto, accettabile.
2. **(Minor) Riproducibilità: snippet del ramo di `probe.sh` e comandi V4.** INDIRIZZATO. Nuova sezione «Come ripetere gli esperimenti» con lo snippet (`event` e `input` sono le variabili reali di `spikes/hookprobe/probe.sh:3,6`; il percorso `hs.txt` coincide con `spikes/run-p3a-experiments.sh:8,17`) e i comandi V4 con `worktree add/remove`.
3. **(Minor) «CLAUDE_PLUGIN_ROOT vale negli hook» non provata.** INDIRIZZATO. La riga V2 ora dice che è espanso nel testo delle skill (V1), non è nell'ambiente di Bash, e che l'uso negli hook non è provato da questo task. Aggiunta anche la nota sul limite di SKILLDIR in Conseguenze V1.

### Danni nuovi nel diff della correzione
Nessuno. Solo documentazione; nessun file di codice, test o campione toccato. Nota lieve (Minor, non bloccante): la «controprova sul solo `plugin.json`» è citata nel rapporto ma senza log dedicato tra i file letti; non incide sulla conclusione, già fondata su (a) e (b).

### Osservazioni fuori ambito
Nessuna.

### Verdetto
**Giro di correzione:** Tutti i rilievi indirizzati, nessun danno nuovo Critical/Important.
