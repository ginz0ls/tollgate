# Ri-revisione 2 del giro di correzione finale di B7 (diff 5c0138f..33968ca)

### Verdetti sui rilievi

- **Frase di 8.5 su `launcher_candidates` (nota minore 1)** — INDIRIZZATO. `docs/superpowers/specs/2026-10-08-tollgate-nucleo-design.md:976`: dice che si toglie il primo `--` dal candidato (I1), con gli esempi `npm exec prisma -- migrate deploy` (chiede) e `npm exec supabase -- start` (passa), e conserva il resto di D2, compreso `npx eslint supabase --fix` che chiede (un `supabase` come argomento di un altro programma). I nomi dei test restano veri. La descrizione generale a riga 948 non nomina `--` e non contraddice.
- **Voci chiuse segnate come chiuse nel piano principale (osservazione)** — INDIRIZZATO. `docs/superpowers/plans/2026-10-27-tollgate-b-piano-principale.md` (blocco «A B8, da B7», righe 268-271): `init.py:254`, riga di `test_rules_database.py`, Q46 senza `subTest`, `approve spec $ISSUE`, `STEPS`, riga vuota doppia e il «5 giri» del rapporto portano «(chiusa nel giro finale di B7, 5c0138f)». Le voci non corrette (`tool-results:`, test sempre saltato, `FRONTEND_PROJECT`, ecc.) restano aperte, giustamente. La voce M3 del Task 1 (riga 263) già dice che `npm exec/run supabase -- start` passano.
- **Doppio `--` tra i rinvii a B8 (nota minore 2)** — INDIRIZZATO. Nuova voce «Dalla ri-revisione della revisione finale di B7: doppio `--` (B8)» con `npm exec prisma -- -- migrate deploy`, la causa (si toglie solo il primo `--`) e «già così prima della correzione I1».

### Danni nuovi nel diff della correzione

Nessuno. Solo documenti (2 file, +5/-4). Controllato che l'hash 5c0138f citato esista nel ramo e che ogni voce marcata «chiusa» corrisponda a una voce chiusa nella ri-revisione 1.

### Osservazioni fuori ambito

Nessuna.

### Verdetto

**Giro di correzione:** Tutti i rilievi indirizzati, nessun danno nuovo Critical/Important
