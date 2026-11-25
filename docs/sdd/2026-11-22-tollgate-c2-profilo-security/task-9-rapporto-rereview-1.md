# Task 9, ri-revisione del giro di correzione 1 del rapporto della prova (Fable)

Oggetto: commit `86b3dff` (genitore `3855816`), 7 file: `docs/verifiche/2026-11-22-c2-prova-flusso.md` e i sei `claude.jsonl` di `docs/verifiche/evidenze/c2/flusso/passoN/tentativo-1/`.
Metodo: sola lettura. Diff del rapporto letto una volta da `review-task-9-fix-rapporto.diff`; rapporto, agenti ed evidenze dei due commit letti da copie `git archive` in cartelle `/tmp/tollgate-rev-XXXXXX` (cancellate alla fine) con script Python propri (`python3 -I -B`) e `/usr/bin/grep -ra`. Nessun `claude`, nessuna rete, nessun subagente. Un solo test mirato, sulla copia resa repo privato.

Con «rapporto:N» intendo la riga N del rapporto al commit `86b3dff`.

## Verdetti sui rilievi

**I1. Il «segnale più pulito» attribuito a `rules-security` precaricata con un fatto falso** — INDIRIZZATO.
- `rapporto:111`: la frase «nomina solo gli id» non c'è più. Ora dice che il contenuto lo chiede «per esteso il testo dell'agente dell'area» (`agents/implementer-security.md`, riga 51: verificato, la riga 51 contiene «chi può arrivare al codice cambiato … il raggio d'azione del cambio»), oltre a R-SECURITY-01 e -16 e alla `checklist`, e conclude che il segnale «prova che il profilo manda il task all'agente dell'area … non prova il precaricamento».
- `rapporto:112`: gli id con il contenuto giusto sono l'«indizio forte», perché `reviewer-security.md:55` e `final-security.md:38` elencano solo i numeri (verificato al commit); «la prova resta il titolo nelle trascrizioni».
- `rapporto:80`, `:169`, `:178`: coerenti (prova = titolo con `isMeta: sì` nelle cinque trascrizioni; indizio forte = id citati).
- `rapporto:191`: punto 6 nuovo in «Differenze con il registro del controller»; il conto «sei punti» a `rapporto:184` è aggiornato.
- Riletti la testa (`:1-14`), «Segnali» (`:107-124`), «Scostamenti» (`:164-169`), «Differenze» (`:182-191`): nessun'altra frase dà alle regole un effetto che le evidenze non provano. I punti (a) confronto a tempo costante («non conta»), (b) («provano la decisione 20 e la spec, non `rules-security`») ed (e) erano già prudenti e non sono cambiati.

**m1. «come dice la skill»; 08 e 15 «non si applica»** — INDIRIZZATO. `rapporto:112`: la divisione è «nella skill e anche nel testo degli agenti»; «15 (revisore del task 1) e 08 (revisore del task 2) sono citate come "non si applica"».

**m2. La skill di TDD presentata come effetto della macchina** — INDIRIZZATO. `rapporto:153` (la chiede `agents/implementer-security.md`, riesce perché il plugin è installato), `:175` (limite vero: il testo della skill di terzi è entrato nel contesto dei due implementatori e non è nelle evidenze), `:201`. Resta un numero di riga sbagliato (vedi danni nuovi, n2).

**m3. Fatti senza fonte** — INDIRIZZATO. `rapporto:63`: i 2 test di partenza hanno la fonte (`spikes/c2/flow/tests/test_tokens.py`, «nel repo, non nelle evidenze»; verificato: 2 `def test_`). `rapporto:162`: le tre lunghezze sono tolte, resta «3 risultati sostituiti» con la fonte `togli-pagine.txt`.

**m4. Il costo spiegato con il numero dei giri e non con il perché** — INDIRIZZATO. `rapporto:142` e `:166`. Verifica su `registro-1/events.jsonl` (15 eventi `spec_audit_round`): `outcome` è `findings` per i giri 1-3 della spec e 1-3 del piano, `empty` per i giri 4-9 della spec e 4-6 del piano. `empty` vuol dire davvero «nessun rilievo sopra `minor`» (`bin/tollgate_analysis/auditrules.py:30`: blocker + major + moderate = 0). I giri aperti dopo un giro `empty` sono 5-9 della spec e 5-6 del piano: sette. I token tornano con gli eventi `cost`: 43.093 + 37.589 + 40.450 + 36.674 + 36.423 = 194.229 e 43.393 + 42.515 = 85.908, totale 280.137. I rifiuti per blocker o major sono alle righe 209 di `passo1` e 218 di `passo3`, solo dopo il giro 1 (verificato). Il dato è vero in «Costi» e in «Scostamenti»; la frase di `rapporto:80` che lo riprende ha il numero sbagliato (danni nuovi, n1).

**m5. `rate_limit_event` e `credential_expires_at`** — INDIRIZZATO. Negli stream al commit: zero occorrenze delle due stringhe. Tolte 15 righe `rate_limit_event` (5, 1, 3, 1, 3, 2 per `passo1`…`passo6`) e 6 campi `credential_expires_at` (uno per stream): sono i numeri che `rapporto:200` dichiara, senza valori.

**m6. `f-1-3` «nota di rafforzamento»** — INDIRIZZATO. `rapporto:105`: «rilievo `minor`, tra le note che "non chiedono modifiche"».

**m7. Il `finding-verifier` ha letto la regola dal file** — INDIRIZZATO. `rapporto:105`; la riga 262 di `passo6/tentativo-1/claude.jsonl` contiene `sed -n 39,44p` su `rules-security/SKILL.md` (verificato).

**m8. Righe `init` senza segnale di riduzione** — INDIRIZZATO. In ognuna delle sei righe `init` c'è il campo `nota` «riga ridotta: tolti plugin, skill, server MCP, agenti e comandi non di tollgate»; `rapporto:199` lo dice.

### Controlli chiesti dal controller

- **Nient'altro è cambiato negli stream.** Per ogni stream ho preso il contenuto di `3855816`, tolto le righe `rate_limit_event` e i campi `credential_expires_at`, e l'ho confrontato con quello di `86b3dff` senza il campo `nota` delle righe `init`: identico in tutti e sei, anche nell'ordine delle chiavi. Righe prima → dopo: 1498 → 1493, 36 → 35, 1167 → 1164, 48 → 47, 1205 → 1202, 318 → 316. In ogni stream le righe non identiche byte per byte a una riga di prima sono due: la `init` e il `result`.
- **JSON valido**: ogni riga dei sei `claude.jsonl` è un oggetto JSON valido; newline finale presente.
- **Risultati web**: 9 `tool_result` di `WebFetch`, tutti e 9 il segnaposto (97-115 caratteri); nessun `WebSearch`.
- **Repo pubblico**: `/usr/bin/grep -raciF` di nome utente e host su rapporto ed evidenze: 0 e 0. `/home/` diverso da `/home/USER`: 0. Forme di token nelle evidenze: 0.
- **Numeri di riga ricalcolati**: 63 e 72 di `passo6` (brief con «Lista di controllo dell'area»), 23 (due `[dopo la revisione]`, nessun `[no]`) e 307 (tutte `[sì]`), 262, 209 di `passo1`, 218 di `passo3`: tutti giusti sugli stream committati.
- **Test**: `tests.test_b1_scripts.FlowScriptTest.test_committed_evidence_has_no_long_web_results` sulla copia `git archive 86b3dff`: OK. Il report dell'implementatore nomina i due lanci (`python3.11` e `python3`, 168 test, OK); non li ho ripetuti.
- **Vincoli del giro**: `Esito: riuscita` è alla riga 3; commit nuovo, solo il rapporto e i sei stream, oggetto giusto, riga `Co-Authored-By` di opus.

## Danni nuovi nel diff della correzione

- **n1 (Minor). `rapporto:80`**: «i 15 giri degli avversari … nove dei quali aperti dopo giri senza rilievi sopra `minor`». I giri *senza* rilievi sopra `minor` sono nove (4-9 della spec, 4-6 del piano); quelli *aperti dopo* un giro così sono sette (5-9 e 5-6), come dicono `rapporto:142` e `:166`. La frase mescola i due dati e contraddice le altre due. Correzione: «nove dei quali senza rilievi sopra `minor`» oppure «sette dei quali aperti solo dopo correzioni di note `minor`».
- **n2 (Minor). `rapporto:153`**: «lo chiede `agents/implementer-security.md` (riga 57)». Al commit la chiamata a `superpowers:test-driven-development` è alla riga 58; la 57 è «1. Implementa esattamente ciò che il task specifica». Il numero viene dalla revisione precedente (m2), che lo dava già sbagliato di uno.
- **n3 (Minor). `rapporto:142`**: «`audit prepare` ha rifiutato di andare avanti solo dopo il giro 1 della spec e il giro 1 del piano». Vero per i rifiuti dovuti a blocker o major. In `passo3` c'è un altro rifiuto di `audit prepare`, per un motivo diverso (riga 54: «committa docs/superpowers/reviews/1/spec-approval.md prima del giro del piano»). Basta scrivere «ha rifiutato per rilievi aperti solo dopo…».

Nessun danno Critical né Important.

## Osservazioni fuori ambito

Nessuna.

## Verdetto

I nove rilievi sono chiusi: il difetto di I1 non esiste più e nessun'altra frase gonfia l'effetto delle regole; gli stream sono cambiati solo dove dichiarato. Restano tre imprecisioni minori introdotte dal giro (n1 è la più utile da correggere, perché tocca il dato di m4), che non bloccano.

**Giro di correzione:** Tutti i rilievi indirizzati, nessun danno nuovo Critical/Important
