# Ri-revisione 1 del giro di correzione finale di B7 (diff db2af0e..5c0138f)

### Verdetti sui rilievi

- **I1: `--` dietro un lanciatore non tolto da `launcher_candidates`** — INDIRIZZATO. `bin/tollgate_analysis/bash.py` (`launcher_candidates`, circa 1105-1108) toglie il primo `--` da `argv[i+1:]`. Sonde mie (`effect_reason` con la `EffectsCfg` di `tests/test_bash.py`, comandi solo come testo): chiedono `npm exec prisma -- migrate deploy`, `npx prisma -- migrate deploy`, `pnpm exec prisma -- migrate deploy`, `npm run prisma -- migrate deploy`, `npm exec drizzle-kit -- push`, `npx drizzle-kit -- push`, `npm exec wrangler -- deploy`, `npm exec wrangler -- d1 execute DB --remote`, `yarn prisma -- migrate deploy`, `bunx prisma -- db push`, `npm exec supabase -- db push` (motivo «senza --local»). Passano `npm exec supabase -- start`, `npm run supabase -- start`, `npx prisma -- generate`, `npx supabase -- db push --local`. `supabase -- db push` senza lanciatore chiede ancora («supabase db»). `npx supabase -- --local db push` chiede (opzione sconosciuta prima del sottocomando, corretto). Test: `tests/test_bash.py:209-219` `test_launcher_double_dash_before_service_args`; `python3 -B -m unittest tests.test_bash`: 111 OK. Nessun test esistente modificato.
- **Voce 7 (docstring di `_concrete_paths`)** — INDIRIZZATO. `bin/tollgate_flow/init.py:253-255`, righe sotto i 100. La sola riga lunga rimasta nel file è una stringa, non toccata.
- **Voce 9 (riga di `tests/test_rules_database.py`)** — INDIRIZZATO. Il tuple è spezzato su due righe (`:323-324`); nessuna riga sopra i 100 nel file.
- **Voce 10 (Q46 senza `subTest`)** — INDIRIZZATO. `tests/test_init.py:1781-1793`, due `with self.subTest(area=...)` con gli stessi controlli.
- **Voce 21 (`approve spec $ISSUE` come numero di fette)** — INDIRIZZATO. `spikes/run-b1-flow.sh:127` `SLICES=1`, usata alle righe 224, 259, 508; nessun `approve spec $ISSUE` rimasto. `bash -n` ok; `tests/test_b1_scripts.py:2058-2059` asseriscono `approve spec 1`, restano veri.
- **Voce 23 (`STEPS` inutilizzata)** — INDIRIZZATO. Nessuna occorrenza di `STEPS` nello script.
- **Voce 25 (riga vuota in più)** — INDIRIZZATO. `tests/test_b1_scripts.py` perde una riga vuota prima della sezione `database` (diff, -1).
- **Voce 34 (rapporto: 5 giri, 9 eventi)** — INDIRIZZATO. `docs/verifiche/2026-11-12-b7-prova-flusso.md:42` dice «9 eventi `spec_audit_round`, 5 della spec e 4 del piano», coerente con i 5 giri della spec e i 4 del piano citati al punto 3.
- **Rinvii M1, M2, M3, «da verificare» CLI 2 nel piano principale, e frase di 8.5** — INDIRIZZATO. `docs/superpowers/plans/2026-10-27-tollgate-b-piano-principale.md` blocco «A B8, da B7» (righe 258 e seguenti): quattro voci nuove, una per punto, ognuna con il motivo (M1 opzioni con valore dei sottocomandi; M2 involucri come `dotenv`/`op run`; M3 `SubagentStart` con due task dello stesso tipo, raggiungibilità da verificare; CLI 2 con `db query`/`db advisors` da verificare sulle note di rilascio). Aggiornata anche la voce M3 dei minori del Task 1 (riga 263), corretta: `npx --package supabase supabase start` chiede ancora (sonda confermata), `npm exec/run supabase -- start` ora passano. Spec nucleo 8.5: «il valore di un'opzione globale (`--workdir --local`; le opzioni con valore dei sottocomandi…)», M1 rispettato.

### Danni nuovi nel diff della correzione

Nessuno Critical/Important. Due note minori:
- Minor, `docs/superpowers/specs/2026-10-08-tollgate-nucleo-design.md` (8.5, punto «Dietro un lanciatore `launcher_candidates` non cambia (D2)»): ora è vero solo per i comandi locali; il codice toglie il primo `--`. Frase non aggiornata, nessun effetto sul comportamento.
- Minor, già prima del giro e non peggiorato: `npm exec prisma -- -- migrate deploy` (doppio `--`) passa, perché si toglie solo il primo. Forma inusuale, fuori dai rilievi.

### Osservazioni fuori ambito

- Il piano principale cita ancora come aperte, nella voce «Dai minori del ledger, Task 2-6» (riga 268) e «Task 7» (riga 269), le voci ora corrette: `init.py:254`, riga di `tests/test_rules_database.py`, Q46 senza `subTest`, `approve spec $ISSUE`, `STEPS`, riga vuota doppia, e la riga del rapporto (voce Task 8, riga 271, «5 giri»). Il report dell'implementatore lo dichiara come testo storico non riscritto. Conviene segnarle come chiuse da B7 (giro finale) o toglierle prima del merge.
- La voce del piano per M3 dei minori del Task 1 (riga 263) conserva «M2 `--help`…» e il resto invariati: coerente.

### Verdetto

**Giro di correzione:** Tutti i rilievi indirizzati, nessun danno nuovo Critical/Important.
