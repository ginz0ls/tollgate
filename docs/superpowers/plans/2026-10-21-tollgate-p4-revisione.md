# Revisione del piano P4

Revisore: opus, a contesto pulito, in sola lettura. Ha confrontato il piano `2026-10-21-tollgate-p4-gate.md` e i suoi compagni con il brief di scrittura, la spec rev 24, il piano principale, i triage di P3b e P3c, i fatti GitHub di P0 e il codice di `main`. Data: 21/10/2026.

| Giro | Commit esaminato | Rilievi | Esito |
|---|---|---|---|
| 1 | `32937a0` | 2 critical, 12 important, 15 minor | Verdetto «non pronto». Tutti corretti in `c7d48c2` |
| 2 | `c7d48c2` | C-1 e I-5, I-7 chiusi in parte; 3 important nuovi (N-1, N-2, N-3) e 3 minor | Verdetto «pronto con correzioni». Corretti in `939aa99` |
| 3 | `939aa99` | N-1, N-2, N-3 e i minor chiusi; 1 important nuovo (N-4: firme degli identificativi della base) | Verdetto «pronto con correzioni». Corretto in `49926a9` |
| 4 | `49926a9` | N-4 chiuso | «Critical aperti: nessuno. Important aperti: nessuno.» Verdetto: **pronto** |

## Rilievi del primo giro

**Critical.**
- C-1: uno stato `success` «non applicabile» sullo SHA poteva rendere unibile una PR verso il predefinito mai valutata. Chiuso dalla decisione 5 e dal Task 8 (`guard` applica la stessa regola, N-3).
- C-2: con `pull_request_target`, il checkout senza `ref` prendeva il ramo base della PR. Chiuso dalla decisione 17 e dal Task 11.

**Important.**

| Rilievo | Argomento | Dove è chiuso |
|---|---|---|
| I-1 | DB caricato dall'entrata del CLI | Decisione 1 |
| I-2 | `GH_TOKEN` sui runner | Decisione 17 e V7 |
| I-3 | Download degli artefatti e stati espliciti | Decisione 17 |
| I-4 | `approvals` in locale | Decisione 10 |
| I-5 | Piano cambiato | Decisione 9 e N-1 |
| I-6 | `size_reason` | Decisione 21 |
| I-7 | Identificativi della base | Decisione 12, N-2 e N-4 |
| I-8 | Analisi dei workflow | Decisione 15 |
| I-9 | Componenti contro intestazioni | Decisione 10 |
| I-10 | Login del bot | V1 e decisione 14 |
| I-11 | `../` negli artefatti | Decisione 13 e V8 |
| I-12 | Codice nel repo pubblico | Decisione 25 |

Per I-12 la scelta dell'utente è stata «pubblico solo per la prova».

**Minor.** M-1…M-15, tutti chiusi.

## Copertura

Uno script ha cercato nella tabella «Copertura» del piano ogni voce destinata a P4 e le ha trovate tutte:
- i criteri 10, 11, 18, 21, 22, 27, 29, 30, 32, 33, 34, 35, 36, 39, 41, 42 e 44;
- i punti (1)-(6) dei «Vincoli per P4» di P3b;
- i punti (1)-(6) dei «Contratti verso il gate» di P3c;
- i punti (1)-(6) dei «Vincoli per P4 emersi in P3c»;
- i casi (a)-(d);
- la riga 56 di P3a;
- le righe 4, 47, 68 e 69 del triage di P3b;
- le righe 2, 3, 4, 7, 11, 12, 16, 19, 20, 22, 29, 34 e 39 del triage di P3c.

Le righe 11, 12 e 20 di P3c sono rinviate a P5, ciascuna con il suo motivo.

## Esito

Revisione chiusa: nessun rilievo critical o important aperto.
